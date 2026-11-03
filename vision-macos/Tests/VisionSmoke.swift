import AppKit
import Vision
import CoreGraphics

@main struct VisionSmoke {
    static func main() throws {
        let w = 1200, h = 900
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0, space: colorSpace, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { fatalError("context") }
        context.setFillColor(NSColor.darkGray.cgColor); context.fill(CGRect(x: 0, y: 0, width: w, height: h))
        context.setFillColor(NSColor.white.cgColor); context.fill(CGRect(x: 400, y: 100, width: 400, height: 700))
        let ns = NSGraphicsContext(cgContext: context, flipped: false)
        NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = ns
        let attrs: [NSAttributedString.Key: Any] = [.font: NSFont.boldSystemFont(ofSize: 55), .foregroundColor: NSColor.black]
        ("AJUSTES" as NSString).draw(at: CGPoint(x: 470, y: 650), withAttributes: attrs)
        ("CONTINUAR" as NSString).draw(at: CGPoint(x: 450, y: 300), withAttributes: attrs)
        NSGraphicsContext.restoreGraphicsState()
        guard let image = context.makeImage() else { fatalError("image") }
        let handler = VNImageRequestHandler(cgImage: image)
        let rect = VNDetectRectanglesRequest(); rect.maximumObservations = 8; rect.minimumConfidence = 0.55; rect.minimumAspectRatio = 0.30; rect.maximumAspectRatio = 0.85; rect.minimumSize = 0.12
        let text = VNRecognizeTextRequest(); text.recognitionLevel = .accurate; text.usesLanguageCorrection = false; text.recognitionLanguages = ["en-US", "es-ES"]
        try handler.perform([rect]); try handler.perform([text])
        let found = (text.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ")
        guard !(rect.results ?? []).isEmpty, found.localizedCaseInsensitiveContains("AJUSTES"), found.localizedCaseInsensitiveContains("CONTINUAR") else { fatalError("Vision did not recognize expected rectangle and text: \(found)") }
        print("Vision smoke test passed: screen rectangle and text detected")
    }
}
