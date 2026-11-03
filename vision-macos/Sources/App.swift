import AppKit
import AVFoundation
import SwiftUI

struct CameraPreview: NSViewRepresentable {
    let session: AVCaptureSession
    func makeNSView(context: Context) -> PreviewView {
        let view = PreviewView(); view.preview.session = session; view.preview.videoGravity = .resizeAspect
        return view
    }
    func updateNSView(_ nsView: PreviewView, context: Context) {
        nsView.preview.session = session
        if let connection = nsView.preview.connection, connection.isVideoMirroringSupported {
            connection.automaticallyAdjustsVideoMirroring = false
            connection.isVideoMirrored = false
        }
    }
    final class PreviewView: NSView {
        let preview = AVCaptureVideoPreviewLayer()
        override init(frame: NSRect) { super.init(frame: frame); wantsLayer = true; layer?.backgroundColor = NSColor.black.cgColor; layer?.addSublayer(preview) }
        required init?(coder: NSCoder) { fatalError("init(coder:) is not used") }
        override func layout() { super.layout(); preview.frame = bounds }
    }
}

struct VisionView: View {
    @ObservedObject var model: CameraModel
    private let cornerNames = ["↖", "↗", "↘", "↙"]
    var body: some View {
        GeometryReader { geo in
            let mapping = ImageMapping(image: model.imageSize, view: geo.size)
            ZStack(alignment: .topLeading) {
                CameraPreview(session: model.session).frame(width: geo.size.width, height: geo.size.height)
                if !model.running {
                    VStack(spacing: 12) {
                        Image(systemName: "camera.viewfinder").font(.system(size: 46, weight: .light)).foregroundColor(.white.opacity(0.7))
                        Text("Tu cámara aparecerá aquí").font(.title3.weight(.medium)).foregroundColor(.white)
                        Text("Coloca el iPhone con la pantalla visible.").foregroundColor(.white.opacity(0.65))
                    }.frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                if let q = model.quad, q.isValid {
                    Path { path in
                        let pts = q.points.map(mapping.display)
                        path.move(to: pts[0]); pts.dropFirst().forEach { path.addLine(to: $0) }; path.closeSubpath()
                    }.stroke(Color.mint, style: StrokeStyle(lineWidth: 2, dash: [7, 4]))
                    ForEach(Array(q.cornerTargets.enumerated()), id: \.offset) { i, p in
                        Text(cornerNames[i]).font(.caption.bold()).foregroundColor(.black)
                            .frame(width: 22, height: 22).background(Color.mint, in: Circle())
                            .position(mapping.display(p))
                    }
                    ForEach(model.labels) { label in
                        Circle().fill(Color.orange.opacity(0.85)).frame(width: 7, height: 7).position(mapping.display(label.center))
                    }
                }
                ForEach(Array(model.calibrationPoints.enumerated()), id: \.offset) { i, p in
                    Text("\(i+1)").font(.caption.bold()).foregroundColor(.black)
                        .frame(width: 24, height: 24).background(Color.yellow, in: Circle()).position(mapping.display(p))
                }
                if let point = model.cursor {
                    ZStack {
                        Circle().stroke(Color.white.opacity(0.4), lineWidth: 1).frame(width: 40, height: 40)
                        Circle().fill(Color(red: 1, green: 0.35, blue: 0.22).opacity(0.22)).frame(width: 30, height: 30)
                        Circle().stroke(Color(red: 1, green: 0.35, blue: 0.22), lineWidth: 3).frame(width: 19, height: 19)
                        Circle().fill(.white).frame(width: 4, height: 4)
                    }.position(mapping.display(point)).animation(.easeInOut(duration: 0.55), value: point)
                }
            }
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onEnded { event in
                guard let p = mapping.imagePoint(event.location) else { return }
                if model.isCalibrating { model.addCalibrationPoint(p) } else { model.moveToPoint(p) }
            })
        }
        .background(Color.black)
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(.white.opacity(0.1), lineWidth: 1))
    }
}

struct ContentView: View {
    @StateObject private var model = CameraModel()
    private let names = ["↖  Arriba izquierda", "↗  Arriba derecha", "↘  Abajo derecha", "↙  Abajo izquierda"]
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("LIVING IN A CAT WORLD  /  EXPERIMENTO 01").font(.system(size: 10, weight: .bold, design: .monospaced)).tracking(1.5).foregroundColor(.mint)
                    Text("Los ojos del robot.").font(.system(size: 30, weight: .semibold, design: .rounded))
                    Text("Observa una pantalla y mueve un cursor virtual.").foregroundColor(.secondary)
                }
                Spacer()
                Label("SOLO SIMULACIÓN", systemImage: "hand.raised.fill").font(.system(size: 10, weight: .bold)).padding(.horizontal, 12).padding(.vertical, 8).background(Color.orange.opacity(0.14), in: Capsule()).foregroundColor(.orange)
            }
            HStack(alignment: .top, spacing: 18) {
                VStack(alignment: .leading, spacing: 12) {
                    VisionView(model: model).aspectRatio(16/10, contentMode: .fit)
                    HStack(alignment: .top, spacing: 8) {
                        Circle().fill(model.quad == nil ? Color.orange : Color.mint).frame(width: 7, height: 7).padding(.top, 5)
                        Text(model.status).font(.callout).foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true)
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }.frame(maxWidth: .infinity)
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("01  CÁMARA").font(.caption.bold()).foregroundColor(.secondary)
                        Picker("Cámara", selection: $model.cameraID) {
                            if model.cameras.isEmpty { Text("Sin cámaras").tag("") }
                            ForEach(model.cameras, id: \.uniqueID) { camera in Text(camera.localizedName).tag(camera.uniqueID) }
                        }.labelsHidden().disabled(model.running)
                        HStack {
                            Button(model.running ? "Detener" : "Iniciar cámara") { if model.running { model.stop() } else { model.start() } }.buttonStyle(.borderedProminent).tint(.mint)
                            Button("Actualizar") { model.refreshCameras() }.disabled(model.running)
                        }
                    }
                    Divider()
                    VStack(alignment: .leading, spacing: 8) {
                        Text("02  PANTALLA").font(.caption.bold()).foregroundColor(.secondary)
                        Text(model.manualMode ? "Calibración manual" : "Detección automática").font(.callout.weight(.medium))
                        HStack { Button("Marcar 4 esquinas") { model.beginCalibration() }; Button("Automático") { model.autoDetect() } }.disabled(!model.running)
                        if model.isCalibrating { Text("Punto \(model.calibrationPoints.count + 1) de 4").font(.caption).foregroundColor(.yellow) }
                    }
                    Divider()
                    VStack(alignment: .leading, spacing: 8) {
                        Text("03  DESTINO VIRTUAL").font(.caption.bold()).foregroundColor(.secondary)
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 7) {
                            ForEach(0..<4) { i in Button(names[i]) { model.stopCycle(); model.moveToCorner(i) }.frame(maxWidth: .infinity).disabled(model.quad == nil) }
                        }
                        Button(model.cycling ? "Detener recorrido" : "Recorrer esquinas") { model.toggleCycle() }.disabled(model.quad == nil)
                        Text("Destino: \(model.cursorLabel)").font(.caption).foregroundColor(.secondary).lineLimit(2)
                        Text("También puedes hacer clic dentro de la pantalla en el video.").font(.caption).foregroundColor(.secondary)
                    }
                    Divider()
                    VStack(alignment: .leading, spacing: 7) {
                        HStack { Text("TEXTO DETECTADO").font(.caption.bold()).foregroundColor(.secondary); Spacer(); Text("\(model.labels.count)").font(.caption.monospacedDigit()).foregroundColor(.secondary) }
                        Text("Selecciona un texto para apuntar a él. No todos los textos son botones.").font(.caption).foregroundColor(.secondary)
                        if model.labels.isEmpty { Text("Aún no hay texto visible.").font(.caption).foregroundColor(.secondary).padding(.vertical, 4) }
                        else {
                            ScrollView { LazyVStack(alignment: .leading, spacing: 3) {
                                ForEach(model.labels) { label in Button(action: { model.moveToLabel(label) }) { HStack { Text(label.text).lineLimit(2).multilineTextAlignment(.leading); Spacer(); Image(systemName: "arrow.up.left") }.frame(maxWidth: .infinity, alignment: .leading) }.buttonStyle(.plain).padding(7).background(.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 6)) }
                            }}.frame(maxHeight: 150)
                        }
                    }
                    Spacer(minLength: 0)
                }.frame(width: 290).padding(17).background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 18))
            }
            HStack {
                Text("La imagen se procesa en esta Mac. No se guarda ni se envía.")
                Spacer()
                Text("PROTOTIPO VISUAL · SIN CONTROL FÍSICO")
            }.font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundColor(.secondary)
        }
        .padding(24).frame(minWidth: 980, minHeight: 730).background(Color(red: 0.06, green: 0.075, blue: 0.085))
        .preferredColorScheme(.dark)
        .onDisappear { model.stop() }
    }
}

@main struct CatVisionApp: App {
    var body: some Scene { WindowGroup("Cat Vision · Living in a Cat World") { ContentView() }.windowResizability(.contentMinSize) }
}
