import AppKit
import AVFoundation
import Combine
import CoreImage
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
    @Published var status = "Elige una cámara y pulsa Iniciar cámara."
    @Published var quad: ScreenQuad?
    @Published var labels: [DetectedLabel] = []
    @Published var imageSize = CGSize(width: 1280, height: 720)
    @Published var cursor: CGPoint?
    @Published var cursorLabel = "Sin destino"
    @Published var isCalibrating = false
    @Published var calibrationPoints: [CGPoint] = []
    @Published var manualMode = false
    @Published var cycling = false
    let session = AVCaptureSession()
    private let captureQueue = DispatchQueue(label: "cat.camera.capture")
    private let sessionQueue = DispatchQueue(label: "cat.camera.session")
    private var lastAnalysis: CFTimeInterval = 0
    private var manualQuad: ScreenQuad?
    private var generation = 0
    private var cornerIndex = 0
    private var timer: Timer?

    override init() { super.init(); refreshCameras() }
    func refreshCameras() {
        let discovery = AVCaptureDevice.DiscoverySession(deviceTypes: [.builtInWideAngleCamera, .external], mediaType: .video, position: .unspecified)
        cameras = discovery.devices
        if !cameras.contains(where: { $0.uniqueID == cameraID }) { cameraID = cameras.first?.uniqueID ?? "" }
    }
    func start() {
        guard !cameraID.isEmpty else { status = "No se encontró ninguna cámara. Conéctala y pulsa Actualizar."; return }
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: configure()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async { if granted { self?.configure() } else { self?.status = "Permite el acceso a la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara." } }
            }
        default: status = "Permite el acceso a la cámara en Ajustes del Sistema → Privacidad y seguridad → Cámara."
        }
    }
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
                guard self.session.canAddInput(input), self.session.canAddOutput(output) else {
                    self.session.commitConfiguration(); throw CameraError.unavailable
                }
                self.session.addInput(input); self.session.addOutput(output)
                if let connection = output.connection(with: .video), connection.isVideoMirroringSupported { connection.automaticallyAdjustsVideoMirroring = false; connection.isVideoMirrored = false }
                self.session.commitConfiguration()
                self.session.startRunning()
                DispatchQueue.main.async {
                    guard currentGeneration == self.generation else { return }
                    self.running = true
                    self.status = "Apunta la cámara hacia el iPhone."
                }
            } catch {
                DispatchQueue.main.async { self.running = false; self.status = "No se pudo iniciar la cámara: \(error.localizedDescription)" }
            }
        }
    }
    func stop() {
        generation += 1
        stopCycle(); running = false; status = "Cámara detenida."
        quad = nil; labels = []; cursor = nil; calibrationPoints = []; isCalibrating = false; manualMode = false
        captureQueue.async { [weak self] in self?.manualQuad = nil }
        sessionQueue.async { [weak self] in self?.session.stopRunning() }
    }
    func beginCalibration() {
        guard running else { status = "Inicia la cámara para calibrar."; return }
        stopCycle(); isCalibrating = true; manualMode = true; calibrationPoints = []; quad = nil; labels = []; cursor = nil
        captureQueue.async { [weak self] in self?.manualQuad = nil }
        status = "Marca las esquinas de la pantalla: superior izquierda, superior derecha, inferior derecha, inferior izquierda."
    }
    func addCalibrationPoint(_ point: CGPoint) {
        guard isCalibrating else { return }
        calibrationPoints.append(point)
        if calibrationPoints.count == 4 {
            let candidate = ScreenQuad(points: calibrationPoints)
            guard candidate.isValid else { calibrationPoints = []; status = "Las esquinas no forman una pantalla válida. Márcalas otra vez en orden."; return }
            quad = candidate; isCalibrating = false
            captureQueue.async { [weak self] in self?.manualQuad = candidate }
            status = "Pantalla calibrada. Selecciona una esquina o un texto detectado."
        }
    }
    func autoDetect() {
        stopCycle(); isCalibrating = false; manualMode = false; calibrationPoints = []; quad = nil; labels = []; cursor = nil
        captureQueue.async { [weak self] in self?.manualQuad = nil }
        status = running ? "Buscando un rectángulo. Si se equivoca, usa calibración manual." : "Inicia la cámara para detectar la pantalla."
    }
    func moveToCorner(_ index: Int) {
        guard let quad = quad, quad.isValid else { status = "Primero detecta o calibra la pantalla."; return }
        let names = ["Superior izquierda", "Superior derecha", "Inferior derecha", "Inferior izquierda"]
        guard quad.cornerTargets.indices.contains(index) else { return }
        cursor = quad.cornerTargets[index]; cursorLabel = names[index]
    }
    func moveToLabel(_ label: DetectedLabel) {
        stopCycle(); cursor = label.center; cursorLabel = label.text
    }
    func moveToPoint(_ point: CGPoint) {
        guard let quad = quad, quad.contains(point) else { return }
        stopCycle(); cursor = point; cursorLabel = "Punto manual"
    }
    func toggleCycle() {
        if cycling { stopCycle(); return }
        guard let quad = quad, quad.isValid else { status = "Primero detecta o calibra la pantalla."; return }
        cycling = true; cornerIndex = 0; moveToCorner(0)
        timer = Timer.scheduledTimer(withTimeInterval: 1.6, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            guard self.quad?.isValid == true else { self.stopCycle(); return }
            self.cornerIndex = (self.cornerIndex + 1) % 4; self.moveToCorner(self.cornerIndex)
        }
    }
    func stopCycle() { timer?.invalidate(); timer = nil; cycling = false }
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let buffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let now = CACurrentMediaTime()
        guard now - lastAnalysis >= 0.9 else { return }
        lastAnalysis = now
        let width = CVPixelBufferGetWidth(buffer), height = CVPixelBufferGetHeight(buffer)
        let handler = VNImageRequestHandler(cvPixelBuffer: buffer, orientation: .up)
        let rectangles = VNDetectRectanglesRequest()
        rectangles.maximumObservations = 8; rectangles.minimumConfidence = 0.55
        rectangles.minimumAspectRatio = 0.30; rectangles.maximumAspectRatio = 0.85; rectangles.minimumSize = 0.12
        let text = VNRecognizeTextRequest()
        text.recognitionLevel = .accurate; text.usesLanguageCorrection = false
        text.recognitionLanguages = ["en-US", "es-ES"]
        do {
            if manualQuad == nil { try handler.perform([rectangles]) }
            let detected = rectangles.results?.compactMap { r -> ScreenQuad? in
                let q = ScreenQuad(points: [r.topLeft, r.topRight, r.bottomRight, r.bottomLeft])
                return q.isValid ? q : nil
            }.max { a, b in
                let aw = abs(a.points[1].x-a.points[0].x) + abs(a.points[2].x-a.points[3].x)
                let bw = abs(b.points[1].x-b.points[0].x) + abs(b.points[2].x-b.points[3].x)
                return aw < bw
            }
            let chosen = manualQuad ?? detected
            var found: [DetectedLabel] = []
            if let chosen = chosen {
                try handler.perform([text])
                found = (text.results ?? []).compactMap { result in
                    guard let candidate = result.topCandidates(1).first, candidate.confidence >= 0.35 else { return nil }
                    let value = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
                    let p = CGPoint(x: result.boundingBox.midX, y: result.boundingBox.midY)
                    guard !value.isEmpty, chosen.contains(p) else { return nil }
                    return DetectedLabel(text: String(value.prefix(80)), center: p)
                }.sorted { $0.center.y > $1.center.y }
            }
            DispatchQueue.main.async { [weak self] in
                guard let self = self, self.running else { return }
                self.imageSize = CGSize(width: width, height: height)
                guard !self.isCalibrating else { return }
                if !self.manualMode { self.quad = chosen }
                self.labels = found
                if self.quad == nil { self.stopCycle(); self.cursor = nil; self.status = "No se detecta la pantalla. Prueba otra luz o calibra las cuatro esquinas." }
                else if !self.cycling { self.status = self.manualMode ? "Pantalla calibrada. El texto detectado puede no ser un botón." : "Rectángulo detectado. Comprueba que coincida con la pantalla." }
            }
        } catch {
            DispatchQueue.main.async { [weak self] in self?.status = "No se pudo analizar la imagen: \(error.localizedDescription)" }
        }
    }
    enum CameraError: LocalizedError { case unavailable; var errorDescription: String? { "La cámara no está disponible." } }
}
