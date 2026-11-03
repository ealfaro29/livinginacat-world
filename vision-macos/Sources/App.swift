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
                if model.showElements && model.hasScreen && !model.calibrating {
                    ForEach(model.labels) { label in
                        RoundedRectangle(cornerRadius: 3)
                            .stroke(Color.mint.opacity(0.8), lineWidth: 1.5)
                            .frame(width: max(2, label.targetBounds.width * map.fitted.width), height: max(2, label.targetBounds.height * map.fitted.height))
                            .position(map.display(label.center)).allowsHitTesting(false)
                    }
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
                        Circle().stroke(model.isClicking ? Color.mint : Color.orange, lineWidth: 3).frame(width: 19, height: 19)
                        Circle().fill(.white).frame(width: 4, height: 4)
                    }.scaleEffect(model.isClicking ? 1.5 : 1)
                        .animation(.easeOut(duration: 0.18), value: model.isClicking)
                        .position(map.display(p)).animation(.easeInOut(duration: 0.45), value: p)
                        .allowsHitTesting(false)
                }
                if !model.status.isEmpty {
                    VStack { Spacer(); Text(model.status).font(.callout).multilineTextAlignment(.center).padding(12).background(.black.opacity(0.75), in: RoundedRectangle(cornerRadius: 10)).padding(18) }
                        .frame(maxWidth: .infinity, maxHeight: .infinity).allowsHitTesting(false)
                }
            }
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onEnded { event in
                guard model.image != nil, let p = map.imagePoint(event.location) else { return }
                model.addCalibrationPoint(p)
            })
            .contextMenu {
                if model.labels.isEmpty { Text("Sin texto detectado") }
                else { ForEach(model.labels) { label in Button(label.text) { model.selectLabel(label) } } }
            }
        }
        .background(.black).clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct ContentView: View {
    @StateObject private var model = CameraModel()
    private let cornerNames = ["Arriba izquierda", "Arriba derecha", "Abajo derecha", "Abajo izquierda"]
    private let cornerArrows = ["↖", "↗", "↘", "↙"]
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Pantalla del iPhone").font(.headline)
                    Spacer()
                    if model.running { Circle().fill(Color.orange).frame(width: 7, height: 7); Text("Cámara activa").font(.caption).foregroundColor(.secondary) }
                }
                ScreenView(model: model).frame(maxWidth: .infinity, maxHeight: .infinity)
                Text(model.clickFeedback.isEmpty ? "Vista y clics simulados · Sin controlar el teléfono" : model.clickFeedback)
                    .font(.caption).foregroundColor(model.clickFeedback.isEmpty ? .secondary : .mint).lineLimit(2)
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Controles").font(.title2.bold())
                    GroupBox("Cámara") {
                        VStack(alignment: .leading, spacing: 10) {
                            Picker("Cámara", selection: $model.cameraID) {
                                ForEach(model.cameras, id: \.uniqueID) { camera in Text(camera.localizedName).tag(camera.uniqueID) }
                            }.onChange(of: model.cameraID) { _, _ in model.restart() }
                            HStack {
                                Button(model.isStarting ? "Iniciando…" : (model.running ? "Detener cámara" : "Iniciar cámara")) { model.running ? model.stop() : model.start() }.disabled(model.isStarting)
                                Button("Actualizar cámaras") { model.refreshCameras() }
                            }
                            HStack { Text("Enfoque"); Slider(value: Binding(get: { model.focus }, set: { model.focus = $0; model.setFocus($0) }), in: 0...1).disabled(!model.focusSupported)
                                Button("Auto") { model.enableAutoFocus() }.disabled(!model.focusSupported) }
                            HStack { Text("Brillo"); Slider(value: Binding(get: { model.brightness }, set: { model.brightness = $0; model.setBrightness($0) }), in: 0...1).disabled(!model.brightnessSupported) }
                            Button("Intentar apagar la luz", systemImage: "lightbulb.slash") { model.retryLight() }.disabled(!model.running || model.lightBusy)
                            if !model.lightMessage.isEmpty { Text(model.lightMessage).font(.caption).foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true) }
                            if !model.focusMessage.isEmpty && model.running { Text(model.focusMessage).font(.caption).foregroundColor(.secondary) }
                        }.padding(.vertical, 4)
                    }
                    GroupBox("Encuadre y cursor") {
                        VStack(alignment: .leading, spacing: 10) {
                            if model.calibrating {
                                Text("Punto \(min(model.calibrationPoints.count + 1, 4))/4: \(cornerNames[min(model.calibrationPoints.count, 3)])").font(.callout.bold()).foregroundColor(.yellow)
                                Text("Haz clic en esa esquina del iPhone en la imagen.").font(.caption).foregroundColor(.secondary)
                                HStack { Button("Deshacer") { model.undoCalibrationPoint() }.disabled(model.calibrationPoints.isEmpty); Button("Cancelar") { model.cancelCalibration() } }
                            } else {
                                HStack { Button("Marcar 4 esquinas", systemImage: "viewfinder") { model.beginCalibration() }.disabled(!model.running)
                                    Button("Girar", systemImage: "rotate.right") { model.rotate() }.disabled(!model.running) }
                                HStack {
                                    Text("Cursor:").font(.caption).foregroundColor(.secondary)
                                    ForEach(0..<4) { i in
                                        Button(cornerArrows[i]) { model.chooseCorner(i) }.help(cornerNames[i]).accessibilityLabel("Cursor: \(cornerNames[i])").disabled(!model.hasScreen)
                                    }
                                    Button(model.cycling ? "Detener" : "Recorrer") { model.toggleCycle() }.disabled(!model.hasScreen)
                                }
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 4)
                    }
                    GroupBox("Elementos detectados · \(model.labels.count)") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Selecciona un elemento para mover el cursor y simular un clic.").font(.caption).foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true)
                            Toggle("Mostrar recuadros", isOn: $model.showElements).toggleStyle(.checkbox)
                            if model.labels.isEmpty {
                                Text(model.hasScreen ? "Buscando texto en la pantalla…" : "Primero encuadra la pantalla del iPhone.")
                                    .font(.caption).foregroundColor(.secondary).frame(maxWidth: .infinity, minHeight: 80, alignment: .center)
                            } else {
                                ScrollView {
                                    LazyVStack(spacing: 4) {
                                        ForEach(model.labels) { label in
                                            Button { model.selectLabel(label) } label: {
                                                HStack { Text(label.text).multilineTextAlignment(.leading).lineLimit(2); Spacer(); if label.iconBounds != nil { Text("Icono").font(.caption2).foregroundColor(.mint) }; Image(systemName: "cursorarrow.click") }
                                                    .frame(maxWidth: .infinity, alignment: .leading).padding(8).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 6))
                                            }.buttonStyle(.plain)
                                        }
                                    }
                                }.frame(minHeight: 120, maxHeight: 260)
                            }
                            Text("Las posiciones de iconos se estiman visualmente; revisa los recuadros. Otros textos se apuntan directamente.").font(.caption2).foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true)
                        }.frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 4)
                    }
                }.padding(.trailing, 4)
            }.frame(width: 340)
        }
        .padding(16).frame(minWidth: 780, minHeight: 620).background(Color(red: 0.055, green: 0.06, blue: 0.07))
        .preferredColorScheme(.dark)
        .onAppear { model.start() }.onDisappear { model.stop() }
        .background {
            Group {
                Button("") { model.chooseCorner(0) }.keyboardShortcut("1", modifiers: [])
                Button("") { model.chooseCorner(1) }.keyboardShortcut("2", modifiers: [])
                Button("") { model.chooseCorner(2) }.keyboardShortcut("3", modifiers: [])
                Button("") { model.chooseCorner(3) }.keyboardShortcut("4", modifiers: [])
                Button("") { model.toggleCycle() }.keyboardShortcut(.space, modifiers: [])
            }.hidden()
        }
    }
}

@main struct CatVisionApp: App {
    var body: some Scene { WindowGroup("Cat Vision") { ContentView() }.defaultSize(width: 1100, height: 800).windowResizability(.contentMinSize) }
}
