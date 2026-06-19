import Foundation
import XCTest
@testable import TueAPI

final class CareerModelsTests: XCTestCase {
    func testSearchResponseDecodesPartialFilterContractFromBackend() throws {
        let data = """
        {
          "query": "",
          "page": 0,
          "per_page": 3,
          "total_hits": 444,
          "total_pages": 148,
          "source_url": "https://www.praxisportal.uni-tuebingen.de/candidate/search",
          "filters": {
            "project_types": [
              {"id": 3, "label": "Job", "count": 185}
            ],
            "industries": [
              {"id": 35, "label": "Informationsmanagement, -technologie", "count": 76}
            ]
          },
          "items": [
            {
              "id": 59143,
              "title": "Sportwissenschaftler*in",
              "preview": "Stellenbeschreibung",
              "location": "Schwäbisch Gmünd",
              "project_types": ["Job"],
              "industries": ["Medizin, Gesundheit, Psychologie"],
              "organizations": ["Reha Zentrum Eisele"],
              "created_at": "2026-06-18T14:11:26+02:00",
              "start_date": null,
              "end_date": null,
              "source_url": "https://www.praxisportal.uni-tuebingen.de/projects/59143"
            }
          ]
        }
        """.data(using: .utf8)!

        let response = try JSONDecoder().decode(CareerSearchResponse.self, from: data)

        XCTAssertEqual(response.totalHits, 444)
        XCTAssertEqual(response.filters.projectTypes.map(\.label), ["Job"])
        XCTAssertEqual(response.filters.industries.map(\.id), [35])
        XCTAssertEqual(response.filters.projectSubtypes, [])
        XCTAssertEqual(response.filters.organizations, [])
        XCTAssertEqual(response.filters.postalCodes, [])
        XCTAssertEqual(response.filters.subscriptionTypes, [])
        XCTAssertEqual(response.items.map(\.id), [59143])
    }

    func testFiltersEndpointDecodesMissingOptionalGroupsAsEmptyLists() throws {
        let data = """
        {
          "project_types": [
            {"id": 1, "label": "Internship", "count": 154}
          ],
          "industries": [
            {"id": 49, "label": "Wissenschaftliche Forschung", "count": 42}
          ]
        }
        """.data(using: .utf8)!

        let filters = try JSONDecoder().decode(CareerSearchFilters.self, from: data)

        XCTAssertEqual(filters.projectTypes.count, 1)
        XCTAssertEqual(filters.industries.count, 1)
        XCTAssertTrue(filters.projectSubtypes.isEmpty)
        XCTAssertTrue(filters.organizations.isEmpty)
        XCTAssertTrue(filters.postalCodes.isEmpty)
        XCTAssertTrue(filters.subscriptionTypes.isEmpty)
    }
}
