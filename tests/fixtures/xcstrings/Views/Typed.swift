import Foundation
func demo(count: Int, name: String, ratio: Double) {
    _ = String(localized: "\(count) items", comment: "Cart badge")
    _ = String(localized: "Hello \(name)")
    _ = String(localized: "Ratio \(ratio)")
    _ = String(localized: "Coming Up")
    _ = String(localized: "\(name) has \(count) items")
}

func more() {
    _ = String(localized: "Tap \"Save\" to continue")
}
