import Foundation

extension BackendClient {
    func fetchCareerFilters() async throws -> CareerSearchFilters {
        let url = try makeURL(path: "api/praxisportal/filters", queryItems: [])
        let data = try await get(url)
        return try JSONDecoder().decode(CareerSearchFilters.self, from: data)
    }

    func searchCareerProjects(
        query: String = "",
        projectTypeId: Int? = nil,
        projectSubtypeId: Int? = nil,
        industryId: Int? = nil,
        postalCode: String = "",
        page: Int = 0,
        perPage: Int = 20
    ) async throws -> CareerSearchResponse {
        var queryItems = [
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "per_page", value: "\(perPage)"),
            URLQueryItem(name: "sort", value: "newest")
        ]
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedQuery.isEmpty {
            queryItems.append(URLQueryItem(name: "query", value: trimmedQuery))
        }
        if let projectTypeId {
            queryItems.append(URLQueryItem(name: "project_type_id", value: "\(projectTypeId)"))
        }
        if let projectSubtypeId {
            queryItems.append(URLQueryItem(name: "project_subtype_id", value: "\(projectSubtypeId)"))
        }
        if let industryId {
            queryItems.append(URLQueryItem(name: "industry_id", value: "\(industryId)"))
        }
        let trimmedPostalCode = postalCode.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedPostalCode.isEmpty {
            queryItems.append(URLQueryItem(name: "postal_code", value: trimmedPostalCode))
        }

        let url = try makeURL(path: "api/praxisportal/search", queryItems: queryItems)
        let data = try await get(url)
        return try JSONDecoder().decode(CareerSearchResponse.self, from: data)
    }

    func fetchCareerProject(id: Int) async throws -> CareerProjectDetail {
        let url = try makeURL(path: "api/praxisportal/projects/\(id)", queryItems: [])
        let data = try await get(url)
        return try JSONDecoder().decode(CareerProjectDetail.self, from: data)
    }
}
