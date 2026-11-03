import AppKit
import SwiftUI

struct ScreenView: View {
    @ObservedObject var model: CameraModel
    var body: some View {
        GeometryReader { geo in
            let map = ImageMapping(image: model.imageSize, view: geo.size)
            ZStack(alignment: .topLeading) {
                Color.black
                if let cg = model.image {
                    Image(nsImage: NSImage(cgImage: cg, size: .zero))
                        .resizable().aspectRatio(contentMode: .fit)
                        .frame(width: geo.size.width, height: geo.size.height)
                }
                if model.calibrating {
                    ForEach(Array(model.calibrationPoints.enumerated()), id: \.offset) { i, p in
                        Text("\(i+1)").font(.caption.bold()).foregroundColor(.black)
                            .frame(width: 24, height: 24).background(Color.yellow, in: Circle()).position(map.display(p))
                    }
                }
                if let p = model.cursor, model.hasScreen {
                    ZStack {
                        Circle().stroke(.white.opacity(0.7), lineWidth: 1).frame(width: 32, height: 32)
                        Circle().stroke(Color.orange, lineWidth: 3).frame(width: 19, height: 19)
                        Circle().fill(.white).frame(width: 4, height: 4)
                    }.position(map.display(p)).animation(.easeInOut(duration: 0.45), value: p)
                }
                if !model.status.isEmpty {
                    VStack { Spacer(); Text(model.status).font(.callout).multilineTextAlignment(.center).padding(12).background(.black.opacity(0.75), in: RoundedRectangle(cornerRadius: 10)).padding(18) }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onEnded { event in
                guard model.image != nil, let p = map.imagePoint(event.location) else { return }
                model.addCalibrationPoint(p)
            })
            .contextMenu {
                if model.labels.isEmpty { Text("Sin texto detectado") }
                else {
                    Text("Apuntar a texto detectado")
                    ForEach(model.labels) { label in Button(label.text) { model.selectLabel(label) } }
                }
            }
        }
        .background(.black)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct ContentView: View {
    @StateObject private var model = CameraModel()
    private let cornerNames = ["Arriba izquierda", "Arriba derecha", "Abajo derecha", "Abajo izquierda"]
    private let cornerArrows = ["↖", "↗", "↘", "↙"]
    var body: some View {
        VStack(spacing: 10) {
            ScreenView(model: model).frame(maxWidth: .infinity, maxHeight: .infinity)
            HStack(spacing: 12) {
                Menu {
                    ForEach(model.cameras, id: \.uniqueID) { camera in
                        Button(camera.localizedName) {
                            if model.cameraID != camera.uniqueID { model.cameraID = camera.uniqueID; model.restart() }
                        }
                    }
                    Button("Actualizar cámaras") { model.refreshCameras() }
                } label: { Image(systemName: "camera.fill").frame(width: 24) }
                .help("Elegir cámara")
                if model.running {
                    Circle().fill(Color.orange).frame(width: 7, height: 7)
                        .help(model.lightOff ? "Cámara activa · luz de la cámara apagada" : "Cámara activa")
                }
                Text("Enfoque").font(.callout)
                Slider(value: Binding(get: { model.focus }, set: { model.focus = $0; model.setFocus($0) }), in: 0...1)
                    .disabled(!model.focusSupported).help(model.focusMessage.isEmpty ? "Ajustar la lente de la cámara" : model.focusMessage)
                Button("Auto") { model.enableAutoFocus() }.buttonStyle(.plain)
                    .foregroundColor(model.focusAuto ? .mint : .secondary).disabled(!model.focusSupported)
                Button(action: { model.rotate() }) { Image(systemName: "rotate.right") }.help("Girar pantalla 90°")
            }
            .buttonStyle(.plain).controlSize(.small).padding(.horizontal, 6)
            HStack(spacing: 8) {
                if model.calibrating {
                    Text("Punto \(min(model.calibrationPoints.count + 1, 4))/4: \(cornerNames[min(model.calibrationPoints.count, 3)])")
                        .font(.caption).foregroundColor(.yellow).frame(maxWidth: .infinity, alignment: .leading)
                    Button("Deshacer") { model.undoCalibrationPoint() }.disabled(model.calibrationPoints.isEmpty)
                    Button("Cancelar") { model.cancelCalibration() }
                } else {
                    Button("Marcar 4 esquinas", systemImage: "viewfinder") { model.beginCalibration() }
                        .disabled(!model.running)
                    Spacer(minLength: 0)
                    Text("Cursor:").font(.caption).foregroundColor(.secondary)
                    ForEach(0..<4) { i in
                        Button(cornerArrows[i]) { model.moveToCorner(i) }
                            .help(cornerNames[i]).accessibilityLabel("Cursor: \(cornerNames[i])")
                            .disabled(!model.hasScreen)
                    }
                }
            }
            .buttonStyle(.bordered).controlSize(.small).padding(.horizontal, 6)
            if !model.focusMessage.isEmpty && model.running { Text(model.focusMessage).font(.caption2).foregroundColor(.secondary) }
            if !model.lightMessage.isEmpty && model.running { Text(model.lightMessage).font(.caption2).foregroundColor(.secondary) }
        }
        .padding(12).frame(minWidth: 350, minHeight: 520).background(Color(red: 0.055, green: 0.06, blue: 0.07))
        .preferredColorScheme(.dark)
        .onAppear { model.start() }
        .onDisappear { model.stop() }
        .background {
            Group {
                Button("") { model.moveToCorner(0) }.keyboardShortcut("1", modifiers: [])
                Button("") { model.moveToCorner(1) }.keyboardShortcut("2", modifiers: [])
                Button("") { model.moveToCorner(2) }.keyboardShortcut("3", modifiers: [])
                Button("") { model.moveToCorner(3) }.keyboardShortcut("4", modifiers: [])
                Button("") { model.toggleCycle() }.keyboardShortcut(.space, modifiers: [])
            }.hidden()
        }
    }
}

@main struct CatVisionApp: App {
    var body: some Scene { WindowGroup("Cat Vision") { ContentView() }.defaultSize(width: 480, height: 800).windowResizability(.contentMinSize) }
}
