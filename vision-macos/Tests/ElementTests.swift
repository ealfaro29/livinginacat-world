import Foundation
import CoreGraphics

@main struct ElementTests {
    static func main() {
        let model = CameraModel()
        model.running = true; model.hasScreen = true
        let item = DetectedLabel(text: "Continuar", bounds: CGRect(x: 0.1, y: 0.2, width: 0.4, height: 0.1))
        model.selectLabel(item)
        precondition(abs((model.cursor?.x ?? 0) - 0.3) < 0.0001 && abs((model.cursor?.y ?? 0) - 0.25) < 0.0001)
        RunLoop.main.run(until: Date().addingTimeInterval(0.65))
        precondition(model.isClicking && model.clickFeedback == "Clic simulado: Continuar")
        RunLoop.main.run(until: Date().addingTimeInterval(0.45))
        precondition(!model.isClicking)
        model.selectLabel(item)
        model.moveToCorner(0)
        RunLoop.main.run(until: Date().addingTimeInterval(0.65))
        precondition(!model.isClicking && model.clickFeedback.isEmpty, "Moving the cursor must cancel a pending simulated click")
        print("Element target and simulated click tests passed")
    }
}
