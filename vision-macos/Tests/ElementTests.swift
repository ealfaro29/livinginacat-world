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
        let firstRow = [0.14, 0.38, 0.62, 0.86].map { CGRect(x: $0 - 0.04, y: 0.60, width: 0.08, height: 0.012) }
        let secondRow = [0.14, 0.38, 0.62, 0.86].map { CGRect(x: $0 - 0.04, y: 0.43, width: 0.08, height: 0.012) }
        let widget = CGRect(x: 0.18, y: 0.86, width: 0.15, height: 0.02)
        let boxes = firstRow + secondRow + [widget]
        let targets = IconGrid.targets(for: boxes, imageSize: CGSize(width: 400, height: 850))
        precondition(targets.count == 8 && targets[8] == nil, "Only aligned icon rows should get icon targets")
        guard let photosTarget = targets[2] else { fatalError("Missing Photos icon target") }
        precondition(abs(photosTarget.midX - boxes[2].midX) < 0.001 && photosTarget.minY > boxes[2].maxY)
        let photo = DetectedLabel(text: "Photos", bounds: boxes[2], iconBounds: photosTarget)
        model.selectLabel(photo)
        precondition(model.cursor == CGPoint(x: photosTarget.midX, y: photosTarget.midY), "Cursor should target the icon, not the label")
        precondition(IconGrid.targets(for: firstRow, imageSize: CGSize(width: 400, height: 850)).isEmpty, "A single row does not establish an icon grid")
        print("Element target and simulated click tests passed")
    }
}
