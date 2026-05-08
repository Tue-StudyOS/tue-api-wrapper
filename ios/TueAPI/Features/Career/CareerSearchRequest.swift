import Foundation

struct CareerSearchRequest: Hashable {
    var query = ""
    var projectTypeId: Int?
    var projectSubtypeId: Int?
    var industryId: Int?
    var postalCode: String?
    var page = 0
    var perPage = 20

    mutating func resetPage() {
        page = 0
    }
}
