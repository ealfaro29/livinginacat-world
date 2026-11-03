import AppKit
import AVFoundation
import Combine
import CoreImage
import ImageIO
import Vision

struct DetectedLabel: Identifiable {
    let id = UUID()
    let text: String
    let center: CGPoint
}

final class CameraModel: NSObject, ObservableObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    @Published var cameras: [AVCaptureDevice] = []
    @Published var cameraID = ""
    @Published var running = false
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

    private let session = AVCaptureSession()
    private let captureQueue = DispatchQueue(label: "cat.camera.capture")
    private let sessionQueue = DispatchQueue(label: "cat.camera.session")
    private let visionQueue = DispatchQueue(label: "cat.camera.vision")
    private let textQueue = DispatchQueue(label: "cat.camera.text")
    private let focusQueue = DispatchQueue(label: "cat.camera.focus")
    private let stateLock = NSLock()
    private let imageContext = CIContext(options: [.cacheIntermediates: false])
    private var currentQuad: ScreenQuad?
    private var manualQuad: ScreenQuad?
    private var calibrationActive = false
    private var isAnalyzing = false
    private var isRecognizing = false
    private var lastAnalysis: CFTimeInterval = 0
    private var lastDetected: CFTimeInterval = 0
    private var lastRender: CFTimeInterval = 0
    private var lastRecognition: CFTimeInterval = 0
    private var generation = 0
    private var focusGeneration = 0
    private var focusWork: DispatchWorkItem?
    private var focusMin = 0
    private var focusMax = 0
    private var focusStep = 1
    private var deviceName = ""
    private var cornerIndex = 0
    private var timer: Timer?
    private var manualRotation = 0

    override init() { super.init(); refreshCameras() }
    func refreshCameras() {
        let list = AVCaptureDevice.DiscoverySession(deviceTypes: [.builtInWideAngleCamera, .external], mediaType: .video, position: .unspecified).devices
        cameras = list
        if !list.contains(where: { $0.uniqueID == cameraID }) { cameraID = list.first(where: { $0.deviceType == .external })?.uniqueID ?? list.first?.uniqueID ?? "" }
    }
    func start() {
        guard !cameraID.isEmpty else { status = "Conecta una cámara y vuelve a abrir la app."; return }
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: configure()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in DispatchQueue.main.async {
                if granted { self?.configure() } else { self?.status = "Activa la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara." }
            }}
        default: status = "Activa la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara."
        }
    }
    func restart() { stop(); start() }
    private func configure() {
        let id = cameraID
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
                    self.running = true; self.status = "Buscando la pantalla…"
                    self.deviceName = device.localizedName
                    self.inspectFocus(deviceName: device.localizedName)
                }
            } catch { DispatchQueue.main.async { self.running = false; self.status = "No se pudo iniciar la cámara: \(error.localizedDescription)" } }
        }
    }
    func stop() {
        generation += 1; focusGeneration += 1; focusWork?.cancel(); timer?.invalidate(); timer = nil
        running = false; hasScreen = false; image = nil; cursor = nil; labels = []; calibrating = false; calibrationPoints = []
        focusSupported = false; focusMessage = "Enfoque no disponible"
        stateLock.lock(); currentQuad = nil; manualQuad = nil; calibrationActive = false; lastDetected = 0; stateLock.unlock()
        sessionQueue.async { [weak self] in self?.session.stopRunning() }
    }
    func beginCalibration() {
        guard running else { return }
        timer?.invalidate(); timer = nil; calibrating = true; calibrationPoints = []; hasScreen = false; cursor = nil; labels = []
        stateLock.lock(); currentQuad = nil; manualQuad = nil; calibrationActive = true; stateLock.unlock()
        status = "Marca las 4 esquinas: arriba izquierda, arriba derecha, abajo derecha y abajo izquierda."
    }
    func addCalibrationPoint(_ point: CGPoint) {
        guard calibrating else { cursor = point; return }
        calibrationPoints.append(point)
        if calibrationPoints.count == 4 {
            let q = ScreenQuad(points: calibrationPoints)
            guard q.isValid else { calibrationPoints = []; status = "Esquinas inválidas. Márcalas otra vez en orden."; return }
            stateLock.lock(); manualQuad = q; currentQuad = q; calibrationActive = false; stateLock.unlock()
            calibrating = false; hasScreen = true; calibrationPoints = []; status = ""
        }
    }
    func rotate() {
        rotation = (rotation + 1) % 4
        stateLock.lock(); manualRotation = rotation; stateLock.unlock()
        cursor = nil; labels = []
    }
    func selectLabel(_ label: DetectedLabel) { timer?.invalidate(); timer = nil; cursor = label.center }
    func moveToCorner(_ index: Int) {
        guard hasScreen else { return }
        let pts = [CGPoint(x: 0.04, y: 0.96), CGPoint(x: 0.96, y: 0.96), CGPoint(x: 0.96, y: 0.04), CGPoint(x: 0.04, y: 0.04)]
        guard pts.indices.contains(index) else { return }; cursor = pts[index]
    }
    func toggleCycle() {
        if timer != nil { timer?.invalidate(); timer = nil; return }
        guard hasScreen else { return }
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
        let q = currentQuad, rotation = manualRotation
        let shouldAnalyze = manualQuad == nil && !calibrationActive && !isAnalyzing && now-lastAnalysis >= 1.6
        let shouldRecognize = q != nil && !isRecognizing && now-lastRecognition >= 3.0
        if shouldAnalyze { isAnalyzing = true; lastAnalysis = now }
        if shouldRecognize { isRecognizing = true; lastRecognition = now }
        stateLock.unlock()
        if shouldAnalyze { analyze(buffer) }
        if shouldRecognize, let q = q { recognize(buffer, quad: q, rotation: rotation) }
        guard now - lastRender >= 0.08 else { return }
        lastRender = now
        let source = CIImage(cvPixelBuffer: buffer)
        let outputImage: CIImage
        if let q = q, let corrected = Self.correct(source, quad: q, rotation: rotation) { outputImage = corrected }
        else { outputImage = source }
        guard let cg = imageContext.createCGImage(outputImage, from: outputImage.extent) else { return }
        DispatchQueue.main.async { [weak self] in
            guard let self = self, self.running else { return }
            self.image = cg; self.imageSize = CGSize(width: cg.width, height: cg.height)
        }
    }
    private func recognize(_ buffer: CVPixelBuffer, quad: ScreenQuad, rotation: Int) {
        textQueue.async { [weak self] in
            guard let self = self else { return }
            var found: [DetectedLabel] = []
            if let corrected = Self.correct(CIImage(cvPixelBuffer: buffer), quad: quad, rotation: rotation) {
                let request = VNRecognizeTextRequest()
                request.recognitionLevel = .fast
                request.usesLanguageCorrection = false
                request.recognitionLanguages = ["en-US", "es-ES"]
                if (try? VNImageRequestHandler(ciImage: corrected, orientation: .up).perform([request])) != nil {
                    found = (request.results ?? []).compactMap { observation in
                        guard let candidate = observation.topCandidates(1).first, candidate.confidence >= 0.35 else { return nil }
                        let label = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !label.isEmpty else { return nil }
                        return DetectedLabel(text: String(label.prefix(80)), center: CGPoint(x: observation.boundingBox.midX, y: observation.boundingBox.midY))
                    }.sorted { $0.center.y > $1.center.y }
                }
            }
            self.stateLock.lock(); self.isRecognizing = false; let currentRotation = self.manualRotation; self.stateLock.unlock()
            DispatchQueue.main.async {
                guard self.running, self.hasScreen, !self.calibrating, currentRotation == rotation else { return }
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
    private func analyze(_ buffer: CVPixelBuffer) {
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
            if self.manualQuad == nil && !self.calibrationActive {
                if let next = detected {
                    if let old = self.currentQuad {
                        let distance = zip(old.points, next.points).reduce(CGFloat.zero) { $0 + hypot($1.0.x - $1.1.x, $1.0.y - $1.1.y) } / 4
                        if distance < 0.12 {
                            self.currentQuad = ScreenQuad(points: zip(old.points, next.points).map { pair in
                                let (a, b) = pair
                                return CGPoint(x: a.x * 0.7 + b.x * 0.3, y: a.y * 0.7 + b.y * 0.3)
                            })
                        } else { self.currentQuad = next }
                    } else { self.currentQuad = next }
                    self.lastDetected = CACurrentMediaTime()
                } else if CACurrentMediaTime() - self.lastDetected > 5 { self.currentQuad = nil }
            }
            let effective = self.currentQuad
            self.isAnalyzing = false
            self.stateLock.unlock()
            DispatchQueue.main.async {
                guard self.running && !self.calibrating else { return }
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
