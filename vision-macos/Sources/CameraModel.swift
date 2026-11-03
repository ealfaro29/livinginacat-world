import AppKit
import AVFoundation
import Combine
import CoreImage
import ImageIO
import Vision

struct DetectedLabel: Identifiable {
    let id = UUID()
    let text: String
    let bounds: CGRect
    var iconBounds: CGRect? = nil
    var targetBounds: CGRect { iconBounds ?? bounds }
    var center: CGPoint { CGPoint(x: targetBounds.midX, y: targetBounds.midY) }
}

private struct SavedScreen: Codable {
    let points: [[Double]]
    let width: Int
    let height: Int
    var quad: ScreenQuad? {
        guard points.count == 4, points.allSatisfy({ $0.count == 2 }) else { return nil }
        let value = ScreenQuad(points: points.map { CGPoint(x: $0[0], y: $0[1]) })
        return value.isValid && width > 0 && height > 0 ? value : nil
    }
}

final class CameraModel: NSObject, ObservableObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    @Published var cameras: [AVCaptureDevice] = []
    @Published var cameraID = ""
    @Published var running = false
    @Published var isStarting = false
    @Published var status = "Apunta la cámara al iPhone."
    @Published var image: CGImage?
    @Published var imageSize = CGSize(width: 1280, height: 720)
    @Published var calibrating = false
    @Published var calibrationPoints: [CGPoint] = []
    @Published var hasScreen = false
    @Published var cursor: CGPoint?
    @Published var labels: [DetectedLabel] = []
    @Published var focus = 0.0
    @Published var focusSupported = false
    @Published var focusAuto = true
    @Published var focusMessage = "Enfoque no disponible"
    @Published var rotation = 0
    @Published var lightOff = false
    @Published var lightMessage = ""
    @Published var lightBusy = false
    @Published var brightness = 0.0
    @Published var brightnessSupported = false
    @Published var showElements = true
    @Published var isClicking = false
    @Published var clickFeedback = ""
    @Published var cycling = false

    private let session = AVCaptureSession()
    private let captureQueue = DispatchQueue(label: "cat.camera.capture")
    private let sessionQueue = DispatchQueue(label: "cat.camera.session")
    private let visionQueue = DispatchQueue(label: "cat.camera.vision")
    private let textQueue = DispatchQueue(label: "cat.camera.text")
    private let focusQueue = DispatchQueue(label: "cat.camera.focus")
    private let lightQueue = DispatchQueue(label: "cat.camera.light")
    private let stateLock = NSLock()
    private let imageContext = CIContext(options: [.cacheIntermediates: false])
    private var currentQuad: ScreenQuad?
    private var calibrationBackup: ScreenQuad?
    private var calibrationActive = false
    private var isAnalyzing = false
    private var isRecognizing = false
    private var visionRevision = 0
    private var pendingScreen: SavedScreen?
    private var rawWidth = 0
    private var rawHeight = 0
    private var activeCameraID = ""
    private var lastAnalysis: CFTimeInterval = 0
    private var lastRender: CFTimeInterval = 0
    private var lastRecognition: CFTimeInterval = 0
    private var generation = 0
    private var focusGeneration = 0
    private var focusWork: DispatchWorkItem?
    private var focusMin = 0
    private var focusMax = 0
    private var focusStep = 1
    private var brightnessMin = 0
    private var brightnessMax = 255
    private var brightnessStep = 1
    private var brightnessWork: DispatchWorkItem?
    private var clickSequence = 0
    private var deviceName = ""
    private var cornerIndex = 0
    private var timer: Timer?
    private var manualRotation = 0
    private var lightRestore: (name: String, mode: Int)?
    private var terminationObserver: NSObjectProtocol?

    override init() {
        super.init(); refreshCameras()
        terminationObserver = NotificationCenter.default.addObserver(forName: NSApplication.willTerminateNotification, object: nil, queue: .main) { [weak self] _ in self?.stop() }
    }
    deinit { if let observer = terminationObserver { NotificationCenter.default.removeObserver(observer) } }
    func refreshCameras() {
        let list = AVCaptureDevice.DiscoverySession(deviceTypes: [.builtInWideAngleCamera, .external], mediaType: .video, position: .unspecified).devices
        cameras = list
        if !list.contains(where: { $0.uniqueID == cameraID }) { cameraID = list.first(where: { $0.deviceType == .external })?.uniqueID ?? list.first?.uniqueID ?? "" }
    }
    func start() {
        guard !running, !isStarting else { return }
        guard !cameraID.isEmpty else { status = "Conecta una cámara y vuelve a abrir la app."; return }
        isStarting = true
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: configure()
        case .notDetermined:
            status = "Esperando permiso para usar la cámara…"
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in DispatchQueue.main.async {
                guard self?.isStarting == true else { return }
                if granted { self?.configure() } else { self?.isStarting = false; self?.status = "Activa la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara." }
            }}
        default: isStarting = false; status = "Activa la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara."
        }
    }
    func restart() { stop(); start() }
    private func configure() {
        let id = cameraID
        let saved = UserDefaults.standard.data(forKey: "cat-screen-" + id).flatMap { try? JSONDecoder().decode(SavedScreen.self, from: $0) }
        let savedRotation = UserDefaults.standard.integer(forKey: "cat-rotation-" + id)
        rotation = (savedRotation % 4 + 4) % 4
        stateLock.lock(); visionRevision += 1; activeCameraID = id; pendingScreen = saved; manualRotation = rotation; rawWidth = 0; rawHeight = 0; stateLock.unlock()
        generation += 1
        let currentGeneration = generation
        status = "Iniciando cámara…"
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            do {
                guard let device = AVCaptureDevice(uniqueID: id) else { throw CameraError.unavailable }
                let input = try AVCaptureDeviceInput(device: device)
                let output = AVCaptureVideoDataOutput()
                output.alwaysDiscardsLateVideoFrames = true
                output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
                output.setSampleBufferDelegate(self, queue: self.captureQueue)
                self.session.beginConfiguration()
                for item in self.session.inputs { self.session.removeInput(item) }
                for item in self.session.outputs { self.session.removeOutput(item) }
                self.session.sessionPreset = .high
                guard self.session.canAddInput(input), self.session.canAddOutput(output) else { self.session.commitConfiguration(); throw CameraError.unavailable }
                self.session.addInput(input); self.session.addOutput(output)
                if let c = output.connection(with: .video), c.isVideoMirroringSupported { c.automaticallyAdjustsVideoMirroring = false; c.isVideoMirrored = false }
                self.session.commitConfiguration()
                self.session.startRunning()
                DispatchQueue.main.async {
                    guard currentGeneration == self.generation else { return }
                    self.stateLock.lock(); let screenReady = self.currentQuad != nil; self.stateLock.unlock()
                    self.isStarting = false; self.running = true; self.hasScreen = screenReady
                    self.status = screenReady ? "" : "Buscando la pantalla…"
                    self.deviceName = device.localizedName
                    self.inspectFocus(deviceName: device.localizedName)
                    self.inspectBrightness(deviceName: device.localizedName)
                    self.turnOffLight(deviceName: device.localizedName, generation: currentGeneration)
                }
            } catch { DispatchQueue.main.async { guard currentGeneration == self.generation else { return }; self.isStarting = false; self.running = false; self.status = "No se pudo iniciar la cámara: \(error.localizedDescription)" } }
        }
    }
    func stop() {
        generation += 1; focusGeneration += 1; focusWork?.cancel(); brightnessWork?.cancel(); timer?.invalidate(); timer = nil; cycling = false
        cancelSimulatedClick()
        lightQueue.sync {
            if let saved = lightRestore { _ = lightHelper(name: saved.name, mode: saved.mode); lightRestore = nil }
        }
        lightOff = false; lightBusy = false; lightMessage = ""
        isStarting = false; running = false; hasScreen = false; image = nil; cursor = nil; labels = []; calibrating = false; calibrationPoints = []
        status = "Cámara detenida."
        focusSupported = false; brightnessSupported = false; focusMessage = "Enfoque no disponible"
        stateLock.lock(); currentQuad = nil; calibrationBackup = nil; pendingScreen = nil; visionRevision += 1; calibrationActive = false; stateLock.unlock()
        sessionQueue.async { [weak self] in self?.session.stopRunning() }
    }
    func beginCalibration() {
        guard running else { return }
        guard !calibrating else { return }
        cancelSimulatedClick()
        timer?.invalidate(); timer = nil; cycling = false; calibrating = true; calibrationPoints = []; hasScreen = false; cursor = nil; labels = []; image = nil
        stateLock.lock(); calibrationBackup = currentQuad; currentQuad = nil; pendingScreen = nil; visionRevision += 1; calibrationActive = true; stateLock.unlock()
        status = "Marca las 4 esquinas: arriba izquierda, arriba derecha, abajo derecha y abajo izquierda."
    }
    func undoCalibrationPoint() {
        guard calibrating, !calibrationPoints.isEmpty else { return }
        calibrationPoints.removeLast()
    }
    func cancelCalibration() {
        guard calibrating else { return }
        stateLock.lock(); currentQuad = calibrationBackup; calibrationBackup = nil; calibrationActive = false; visionRevision += 1
        let restored = currentQuad != nil; stateLock.unlock()
        calibrating = false; calibrationPoints = []; hasScreen = restored; image = nil
        status = restored ? "" : "Buscando la pantalla…"
    }
    func addCalibrationPoint(_ point: CGPoint) {
        guard calibrating else { timer?.invalidate(); timer = nil; cycling = false; cancelSimulatedClick(); cursor = point; return }
        calibrationPoints.append(point)
        if calibrationPoints.count == 4 {
            let q = ScreenQuad(points: calibrationPoints)
            guard q.isValid else { calibrationPoints = []; status = "Esquinas inválidas. Márcalas otra vez en orden."; return }
            stateLock.lock(); currentQuad = q; calibrationBackup = nil; calibrationActive = false
            saveScreen(q, width: rawWidth, height: rawHeight, camera: activeCameraID); stateLock.unlock()
            calibrating = false; hasScreen = true; calibrationPoints = []; status = ""
        }
    }
    func rotate() {
        cancelSimulatedClick()
        rotation = (rotation + 1) % 4
        stateLock.lock(); manualRotation = rotation; visionRevision += 1; stateLock.unlock()
        UserDefaults.standard.set(rotation, forKey: "cat-rotation-" + cameraID)
        cursor = nil; labels = []
    }
    private func cancelSimulatedClick() { clickSequence += 1; isClicking = false; clickFeedback = "" }
    func selectLabel(_ label: DetectedLabel) {
        guard hasScreen, !calibrating else { return }
        timer?.invalidate(); timer = nil; cycling = false; cancelSimulatedClick()
        let sequence = clickSequence
        cursor = label.center; clickFeedback = "Moviendo cursor a: \(label.text)"
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            guard let self = self, self.clickSequence == sequence, self.running, self.hasScreen, !self.calibrating else { return }
            self.isClicking = true; self.clickFeedback = "Clic simulado: \(label.text)"
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { [weak self] in
                guard let self = self, self.clickSequence == sequence else { return }
                self.isClicking = false
            }
        }
    }
    func moveToCorner(_ index: Int) {
        guard hasScreen else { return }
        cancelSimulatedClick()
        let pts = [CGPoint(x: 0.04, y: 0.96), CGPoint(x: 0.96, y: 0.96), CGPoint(x: 0.96, y: 0.04), CGPoint(x: 0.04, y: 0.04)]
        guard pts.indices.contains(index) else { return }; cursor = pts[index]
    }
    func chooseCorner(_ index: Int) { timer?.invalidate(); timer = nil; cycling = false; moveToCorner(index) }
    func toggleCycle() {
        if timer != nil { timer?.invalidate(); timer = nil; cycling = false; return }
        guard hasScreen else { return }
        cycling = true
        cornerIndex = 0; moveToCorner(0)
        timer = Timer.scheduledTimer(withTimeInterval: 1.6, repeats: true) { [weak self] _ in
            guard let self = self, self.hasScreen else { self?.timer?.invalidate(); self?.timer = nil; return }
            self.cornerIndex = (self.cornerIndex + 1) % 4; self.moveToCorner(self.cornerIndex)
        }
    }
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let buffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let now = CACurrentMediaTime()
        stateLock.lock()
        rawWidth = CVPixelBufferGetWidth(buffer); rawHeight = CVPixelBufferGetHeight(buffer)
        var restored = false
        if let saved = pendingScreen {
            pendingScreen = nil
            if saved.width == rawWidth, saved.height == rawHeight, let q = saved.quad {
                currentQuad = q; restored = true
            }
        }
        let q = currentQuad, rotation = manualRotation, revision = visionRevision, camera = activeCameraID
        // The phone and camera are stationary: once a screen is found, hold
        // those corners until the user explicitly recalibrates or restarts.
        let shouldAnalyze = currentQuad == nil && !calibrationActive && !isAnalyzing && now-lastAnalysis >= 1.6
        let shouldRecognize = q != nil && !isRecognizing && now-lastRecognition >= 3.0
        if shouldAnalyze { isAnalyzing = true; lastAnalysis = now }
        if shouldRecognize { isRecognizing = true; lastRecognition = now }
        stateLock.unlock()
        if restored { DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.stateLock.lock(); let isCurrent = self.visionRevision == revision; self.stateLock.unlock()
            guard isCurrent, self.running, !self.calibrating else { return }; self.hasScreen = true; self.status = ""
        } }
        if shouldAnalyze { analyze(buffer, revision: revision, camera: camera) }
        if shouldRecognize, let q = q { recognize(buffer, quad: q, rotation: rotation, revision: revision) }
        guard now - lastRender >= 0.08 else { return }
        lastRender = now
        let source = CIImage(cvPixelBuffer: buffer)
        let outputImage: CIImage
        if let q = q, let corrected = Self.correct(source, quad: q, rotation: rotation) { outputImage = corrected }
        else { outputImage = source }
        guard let cg = imageContext.createCGImage(outputImage, from: outputImage.extent) else { return }
        DispatchQueue.main.async { [weak self] in
            guard let self = self, self.running else { return }
            self.stateLock.lock(); let isCurrent = self.visionRevision == revision; self.stateLock.unlock()
            guard isCurrent else { return }
            self.image = cg; self.imageSize = CGSize(width: cg.width, height: cg.height)
        }
    }
    private func recognize(_ buffer: CVPixelBuffer, quad: ScreenQuad, rotation: Int, revision: Int) {
        textQueue.async { [weak self] in
            guard let self = self else { return }
            var found: [DetectedLabel] = []
            if let corrected = Self.correct(CIImage(cvPixelBuffer: buffer), quad: quad, rotation: rotation) {
                let request = VNRecognizeTextRequest()
                request.recognitionLevel = .accurate
                request.usesLanguageCorrection = false
                request.minimumTextHeight = 0.008
                request.recognitionLanguages = ["en-US", "es-ES"]
                if (try? VNImageRequestHandler(ciImage: corrected, orientation: .up).perform([request])) != nil {
                    found = (request.results ?? []).compactMap { observation in
                        guard let candidate = observation.topCandidates(1).first, candidate.confidence >= 0.35 else { return nil }
                        let label = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !label.isEmpty else { return nil }
                        return DetectedLabel(text: String(label.prefix(80)), bounds: observation.boundingBox)
                    }.sorted { $0.bounds.midY > $1.bounds.midY }
                    let targets = IconGrid.targets(for: found.map(\.bounds), imageSize: corrected.extent.size)
                    for (index, target) in targets { found[index].iconBounds = target }
                }
            }
            self.stateLock.lock(); self.isRecognizing = false; let currentRotation = self.manualRotation, currentRevision = self.visionRevision; self.stateLock.unlock()
            DispatchQueue.main.async {
                self.stateLock.lock(); let stillCurrent = self.visionRevision == revision; self.stateLock.unlock()
                guard self.running, self.hasScreen, !self.calibrating, currentRotation == rotation, currentRevision == revision, stillCurrent else { return }
                self.labels = found
            }
        }
    }
    static func correct(_ source: CIImage, quad: ScreenQuad, rotation: Int) -> CIImage? {
        guard quad.isValid, let filter = CIFilter(name: "CIPerspectiveCorrection") else { return nil }
        let size = source.extent
        let vertices = quad.points.map { CIVector(x: size.minX + $0.x * size.width, y: size.minY + $0.y * size.height) }
        filter.setValue(source, forKey: kCIInputImageKey)
        for (key, value) in zip(["inputTopLeft", "inputTopRight", "inputBottomRight", "inputBottomLeft"], vertices) { filter.setValue(value, forKey: key) }
        guard var result = filter.outputImage else { return nil }
        // Start in portrait when the camera sees the phone sideways. The rotate control corrects the remaining ambiguity.
        if result.extent.width > result.extent.height { result = result.oriented(.right) }
        let orientations: [CGImagePropertyOrientation] = [.up, .right, .down, .left]
        return result.oriented(orientations[(rotation % 4 + 4) % 4])
    }
    private func saveScreen(_ quad: ScreenQuad, width: Int, height: Int, camera: String) {
        guard width > 0, height > 0, !camera.isEmpty else { return }
        let record = SavedScreen(points: quad.points.map { [Double($0.x), Double($0.y)] }, width: width, height: height)
        if let data = try? JSONEncoder().encode(record) { UserDefaults.standard.set(data, forKey: "cat-screen-" + camera) }
    }
    private func analyze(_ buffer: CVPixelBuffer, revision: Int, camera: String) {
        let width = CVPixelBufferGetWidth(buffer), height = CVPixelBufferGetHeight(buffer)
        visionQueue.async { [weak self] in
            guard let self = self else { return }
            let request = VNDetectRectanglesRequest()
            request.maximumObservations = 8; request.minimumConfidence = 0.55
            request.minimumAspectRatio = 0.30; request.maximumAspectRatio = 0.85; request.minimumSize = 0.12
            let handler = VNImageRequestHandler(cvPixelBuffer: buffer, orientation: .up)
            let detected: ScreenQuad?
            do {
                try handler.perform([request])
                detected = request.results?.compactMap { r -> ScreenQuad? in
                    let q = ScreenQuad(points: [r.topLeft, r.topRight, r.bottomRight, r.bottomLeft]); return q.isValid ? q : nil
                }.max { a, b in
                    let area: (ScreenQuad) -> CGFloat = { q in abs((q.points[1].x-q.points[0].x)*(q.points[3].y-q.points[0].y) - (q.points[1].y-q.points[0].y)*(q.points[3].x-q.points[0].x)) }
                    return area(a) < area(b)
                }
            } catch { detected = nil }
            self.stateLock.lock()
            let accepted = self.visionRevision == revision && self.currentQuad == nil && !self.calibrationActive && detected != nil
            if accepted, let detected = detected {
                self.currentQuad = detected
                self.saveScreen(detected, width: width, height: height, camera: camera)
            }
            let effective = self.currentQuad
            self.isAnalyzing = false
            self.stateLock.unlock()
            DispatchQueue.main.async {
                self.stateLock.lock(); let isCurrent = self.visionRevision == revision; self.stateLock.unlock()
                guard isCurrent && self.running && !self.calibrating else { return }
                self.hasScreen = effective != nil
                self.status = effective == nil ? "No se detecta la pantalla. Usa Encuadrar para marcar sus esquinas." : ""
                if effective == nil { self.cursor = nil; self.labels = [] }
            }
        }
    }
    private func helper(_ args: [String]) -> (Int32, String) {
        guard let path = Bundle.main.path(forAuxiliaryExecutable: "uvc-util") else { return (-1, "") }
        let process = Process(); process.executableURL = URL(fileURLWithPath: path); process.arguments = args
        let pipe = Pipe(); process.standardOutput = pipe; process.standardError = pipe
        do { try process.run() } catch { return (-1, "") }
        let data = pipe.fileHandleForReading.readDataToEndOfFile(); process.waitUntilExit()
        return (process.terminationStatus, String(data: data, encoding: .utf8) ?? "")
    }
    private func lightHelper(name: String, mode: Int) -> (Int32, String) {
        guard let path = Bundle.main.path(forAuxiliaryExecutable: "c922-led") else { return (-1, "") }
        let process = Process(); process.executableURL = URL(fileURLWithPath: path); process.arguments = [name, String(mode)]
        let pipe = Pipe(); process.standardOutput = pipe; process.standardError = pipe
        do { try process.run() } catch { return (-1, "") }
        let data = pipe.fileHandleForReading.readDataToEndOfFile(); process.waitUntilExit()
        return (process.terminationStatus, String(data: data, encoding: .utf8) ?? "")
    }
    private func turnOffLight(deviceName: String, generation: Int) {
        guard cameras.filter({ $0.localizedName == deviceName }).count == 1, deviceName == "C922 Pro Stream Webcam" else { lightMessage = "Control de luz no disponible para esta cámara."; return }
        lightBusy = true
        lightQueue.async { [weak self] in
            guard let self = self else { return }
            let (result, output) = self.lightHelper(name: deviceName, mode: 0)
            if result == 0, let previous = Int(output.trimmingCharacters(in: .whitespacesAndNewlines)) {
                if self.lightRestore == nil { self.lightRestore = (deviceName, previous) }
            }
            DispatchQueue.main.async {
                guard self.generation == generation, self.running else { return }
                self.lightBusy = false
                self.lightOff = result == 0
                self.lightMessage = result == 0 ? "Comando enviado. Comprueba la luz física." : "La cámara rechazó el comando para apagar la luz."
            }
        }
    }
    func retryLight() { guard running, !lightBusy else { return }; turnOffLight(deviceName: deviceName, generation: generation) }
    private func controlNumber(_ name: String, in output: String) -> Int? {
        let pattern = "(?m)^\\s*" + NSRegularExpression.escapedPattern(for: name) + ":\\s*(-?[0-9]+)"
        guard let regex = try? NSRegularExpression(pattern: pattern), let match = regex.firstMatch(in: output, range: NSRange(output.startIndex..., in: output)), let range = Range(match.range(at: 1), in: output) else { return nil }
        return Int(output[range])
    }
    private func inspectBrightness(deviceName: String) {
        let version = focusGeneration
        brightnessSupported = false
        guard cameras.filter({ $0.localizedName == deviceName }).count == 1 else { return }
        focusQueue.async { [weak self] in
            guard let self = self else { return }
            let (result, output) = self.helper(["-N", deviceName, "-S", "brightness"])
            let low = self.controlNumber("minimum", in: output), high = self.controlNumber("maximum", in: output)
            let step = self.controlNumber("step-size", in: output) ?? 1, value = self.controlNumber("current-value", in: output)
            DispatchQueue.main.async {
                guard self.focusGeneration == version, result == 0, let low = low, let high = high, high > low, let value = value else { return }
                self.brightnessMin = low; self.brightnessMax = high; self.brightnessStep = max(1, step)
                self.brightness = Double(value - low) / Double(high - low); self.brightnessSupported = true
            }
        }
    }
    func setBrightness(_ normalized: Double) {
        guard brightnessSupported else { return }
        brightnessWork?.cancel()
        let raw = Double(brightnessMin) + max(0, min(1, normalized)) * Double(brightnessMax - brightnessMin)
        let steps = Int(((raw - Double(brightnessMin)) / Double(brightnessStep)).rounded())
        let value = min(brightnessMax, max(brightnessMin, brightnessMin + steps * brightnessStep))
        let name = deviceName, version = focusGeneration
        let work = DispatchWorkItem { [weak self] in
            guard let self = self else { return }
            let (result, _) = self.helper(["-N", name, "-s", "brightness=\(value)"])
            if result != 0 { DispatchQueue.main.async { guard self.focusGeneration == version else { return }; self.focusMessage = "No se pudo ajustar el brillo." } }
        }
        brightnessWork = work; focusQueue.asyncAfter(deadline: .now() + 0.18, execute: work)
    }
    private func inspectFocus(deviceName: String) {
        focusGeneration += 1
        let version = focusGeneration
        guard cameras.filter({ $0.localizedName == deviceName }).count == 1 else { focusMessage = "No se puede distinguir entre cámaras con el mismo nombre."; return }
        focusSupported = false; focusMessage = "Comprobando enfoque…"
        focusQueue.async { [weak self] in
            guard let self = self else { return }
            let (status, output) = self.helper(["-N", deviceName, "-S", "focus-abs", "-g", "auto-focus"])
            func number(_ name: String) -> Int? {
                let pattern = "(?m)^\\s*" + NSRegularExpression.escapedPattern(for: name) + ":\\s*(-?[0-9]+)"
                guard let regex = try? NSRegularExpression(pattern: pattern), let m = regex.firstMatch(in: output, range: NSRange(output.startIndex..., in: output)), let range = Range(m.range(at: 1), in: output) else { return nil }
                return Int(output[range])
            }
            let low = number("minimum"), high = number("maximum"), step = number("step-size") ?? 1, value = number("current-value")
            DispatchQueue.main.async {
                guard version == self.focusGeneration else { return }
                guard status == 0, let low = low, let high = high, high > low, let value = value else { self.focusMessage = "Esta cámara no permite enfoque manual."; return }
                self.focusMin = low; self.focusMax = high; self.focusStep = max(1, step)
                self.focus = Double(value-low)/Double(high-low)
                self.focusAuto = output.contains("auto-focus = true")
                self.focusSupported = true; self.focusMessage = ""
            }
        }
    }
    func setFocus(_ normalized: Double) {
        guard focusSupported else { return }
        focusAuto = false; focusWork?.cancel()
        let raw = Double(focusMin) + max(0, min(1, normalized)) * Double(focusMax-focusMin)
        let steps = Int(((raw - Double(focusMin)) / Double(focusStep)).rounded())
        let value = min(focusMax, max(focusMin, focusMin + steps * focusStep))
        let name = deviceName, version = focusGeneration
        let work = DispatchWorkItem { [weak self] in
            guard let self = self else { return }
            let (result, _) = self.helper(["-N", name, "-s", "auto-focus=false", "-s", "focus-abs=\(value)"])
            DispatchQueue.main.async { guard self.focusGeneration == version else { return }; self.focusMessage = result == 0 ? "" : "No se pudo ajustar el enfoque." }
        }
        focusWork = work; focusQueue.asyncAfter(deadline: .now()+0.18, execute: work)
    }
    func enableAutoFocus() {
        guard focusSupported else { return }
        focusWork?.cancel(); let name = deviceName, version = focusGeneration
        focusQueue.async { [weak self] in
            guard let self = self else { return }
            let (result, _) = self.helper(["-N", name, "-s", "auto-focus=true"])
            DispatchQueue.main.async { guard self.focusGeneration == version else { return }; self.focusAuto = result == 0; self.focusMessage = result == 0 ? "" : "No se pudo activar el enfoque automático." }
        }
    }
    enum CameraError: LocalizedError { case unavailable; var errorDescription: String? { "La cámara no está disponible." } }
}
