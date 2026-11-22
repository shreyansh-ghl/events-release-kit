// OCR with macOS Vision. Usage: swift ocr.swift img1.png img2.png ...
// Prints one JSON object per image: {"file": "...", "lines": [{"text": "...", "conf": 0.98, "box": [x, y, w, h]}]}
// Boxes are normalised 0..1 with the origin at the top-left.
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let image = NSImage(contentsOfFile: path),
          let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        FileHandle.standardError.write("cannot read \(path)\n".data(using: .utf8)!)
        exit(1)
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
    var lines: [[String: Any]] = []
    for obs in request.results ?? [] {
        guard let top = obs.topCandidates(1).first else { continue }
        let b = obs.boundingBox
        lines.append(["text": top.string, "conf": top.confidence,
                      "box": [b.origin.x, 1 - b.origin.y - b.height, b.width, b.height]])
    }
    let out: [String: Any] = ["file": path, "lines": lines]
    let data = try JSONSerialization.data(withJSONObject: out)
    print(String(data: data, encoding: .utf8)!)
}
