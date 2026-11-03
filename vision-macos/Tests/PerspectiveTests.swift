import Foundation
import AppKit
import CoreImage

@main struct PerspectiveTests {
    static func main() {
        let source = CIImage(color: CIColor(red: 0.5, green: 0.5, blue: 0.5)).cropped(to: CGRect(x: 0, y: 0, width: 800, height: 600))
        let landscape = ScreenQuad(points: [CGPoint(x: 0.1,y: 0.8),CGPoint(x: 0.9,y: 0.8),CGPoint(x: 0.9,y: 0.2),CGPoint(x: 0.1,y: 0.2)])
        guard let portrait = CameraModel.correct(source, quad: landscape, rotation: 0), let rotated = CameraModel.correct(source, quad: landscape, rotation: 1) else { fatalError("Perspective correction failed") }
        assert(portrait.extent.height > portrait.extent.width, "Landscape camera view should be displayed in portrait")
        assert(rotated.extent.width > rotated.extent.height, "Rotation should swap dimensions")
        let invalid = ScreenQuad(points: [.zero,.zero,.zero,.zero])
        assert(CameraModel.correct(source, quad: invalid, rotation: 0) == nil)
        print("Perspective and rotation tests passed")
    }
}
