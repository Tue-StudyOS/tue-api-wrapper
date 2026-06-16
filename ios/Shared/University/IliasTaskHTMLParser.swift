import Foundation

enum IliasTaskHTMLParser {
    static func parse(_ html: String, pageURL: URL) throws -> [IliasTask] {
        let blocks = IliasHTMLItemParser.blocks(in: html, containingClasses: ["il-item", "il-std-item"])
        let tasks = blocks.compactMap { block -> IliasTask? in
            guard let titleLink = IliasHTMLItemParser.firstActionElement(in: block),
                  let url = IliasHTMLItemParser.resolve(titleLink.url, pageURL: pageURL) else {
                return nil
            }
            let properties = IliasHTMLItemParser.itemProperties(in: block)
            return IliasTask(
                title: titleLink.title,
                url: url.absoluteString,
                itemType: properties["Übung"] ?? properties["Kurs"] ?? properties["Typ"],
                start: properties["Beginn"],
                end: properties["Ende"]
            )
        }

        if tasks.isEmpty, IliasHTMLItemParser.isLoginOrHandoffPage(html) {
            throw UniversityPortalError.parsing("The response did not look like an authenticated ILIAS task overview.")
        }
        return tasks
    }
}
