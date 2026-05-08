import Foundation

struct CareerFacetOption: Decodable, Identifiable, Hashable {
    var id: Int
    var label: String
    var count: Int
}

struct CareerPostalCodeOption: Decodable, Identifiable, Hashable {
    var code: String
    var label: String
    var count: Int
    var location: String?

    var id: String { code }
}

struct CareerSubscriptionType: Decodable, Identifiable, Hashable {
    var id: Int
    var title: String
    var shortName: String

    enum CodingKeys: String, CodingKey {
        case id, title
        case shortName = "short_name"
    }
}

struct CareerSearchFilters: Decodable, Hashable {
    var projectTypes: [CareerFacetOption]
    var projectSubtypes: [CareerFacetOption]
    var industries: [CareerFacetOption]
    var organizations: [CareerFacetOption]
    var postalCodes: [CareerPostalCodeOption]
    var subscriptionTypes: [CareerSubscriptionType]

    enum CodingKeys: String, CodingKey {
        case projectTypes = "project_types"
        case projectSubtypes = "project_subtypes"
        case industries
        case organizations
        case postalCodes = "postal_codes"
        case subscriptionTypes = "subscription_types"
    }
}

struct CareerOrganization: Decodable, Identifiable, Hashable {
    var rawId: Int?
    var name: String
    var logoURL: String?

    var id: String { rawId.map(String.init) ?? name }

    enum CodingKeys: String, CodingKey {
        case rawId = "id"
        case name
        case logoURL = "logo_url"
    }
}

struct CareerProjectSummary: Decodable, Identifiable, Hashable {
    var id: Int
    var title: String
    var preview: String?
    var location: String?
    var projectTypes: [String]
    var industries: [String]
    var organizations: [String]
    var createdAt: String?
    var startDate: String?
    var endDate: String?
    var sourceURL: String

    enum CodingKeys: String, CodingKey {
        case id, title, preview, location, industries, organizations
        case projectTypes = "project_types"
        case createdAt = "created_at"
        case startDate = "start_date"
        case endDate = "end_date"
        case sourceURL = "source_url"
    }
}

struct CareerProjectDetail: Decodable, Identifiable {
    var id: Int
    var title: String
    var location: String?
    var description: String?
    var requirements: String?
    var projectTypes: [String]
    var industries: [String]
    var organizations: [CareerOrganization]
    var createdAt: String?
    var startDate: String?
    var endDate: String?
    var sourceURL: String?

    enum CodingKeys: String, CodingKey {
        case id, title, location, description, requirements, industries, organizations
        case projectTypes = "project_types"
        case createdAt = "created_at"
        case startDate = "start_date"
        case endDate = "end_date"
        case sourceURL = "source_url"
    }
}

struct CareerSearchResponse: Decodable {
    var query: String
    var page: Int
    var perPage: Int
    var totalHits: Int
    var totalPages: Int
    var sourceURL: String
    var filters: CareerSearchFilters
    var items: [CareerProjectSummary]

    enum CodingKeys: String, CodingKey {
        case query, page, filters, items
        case perPage = "per_page"
        case totalHits = "total_hits"
        case totalPages = "total_pages"
        case sourceURL = "source_url"
    }
}

struct CareerUser: Decodable, Identifiable, Hashable {
    var id: Int
    var username: String
    var fullname: String
    var instituteId: Int?

    enum CodingKeys: String, CodingKey {
        case id, username, fullname
        case instituteId = "institute_id"
    }
}

struct CareerSubscriptionQuery: Codable, Hashable {
    var inEnglish = false
    var startDate: String? = nil
    var endDate: String? = nil
    var text: [String] = []
    var industries: [String] = []
    var projectSubtypes: [String] = []
    var postalCode: [String] = []
    var projectTypeId: [String] = []
    var version = "2.0"

    enum CodingKeys: String, CodingKey {
        case text, industries, version
        case inEnglish = "in_english"
        case startDate = "start_date"
        case endDate = "end_date"
        case projectSubtypes = "project_subtypes"
        case postalCode = "postal_code"
        case projectTypeId = "project_type_id"
    }
}

struct CareerSubscription: Decodable, Identifiable, Hashable {
    var id: Int
    var userId: Int
    var queryId: Int
    var subscriptionTypeId: Int
    var active: Bool
    var createdAt: String?
    var updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id, active
        case userId = "user_id"
        case queryId = "query_id"
        case subscriptionTypeId = "subscription_type_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        userId = try container.decodeIfPresent(Int.self, forKey: .userId) ?? 0
        queryId = try container.decodeIfPresent(Int.self, forKey: .queryId) ?? 0
        subscriptionTypeId = try container.decodeIfPresent(Int.self, forKey: .subscriptionTypeId) ?? 1
        if let boolValue = try? container.decodeIfPresent(Bool.self, forKey: .active) {
            active = boolValue
        } else {
            active = (try container.decodeIfPresent(Int.self, forKey: .active) ?? 1) != 0
        }
        createdAt = try container.decodeIfPresent(String.self, forKey: .createdAt)
        updatedAt = try container.decodeIfPresent(String.self, forKey: .updatedAt)
    }
}

struct CareerProjectSelection: Hashable {
    var id: Int
    var title: String
}
