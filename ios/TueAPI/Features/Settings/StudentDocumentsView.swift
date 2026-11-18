import CoreTransferable
import PDFKit
import SwiftUI
import UniformTypeIdentifiers

struct StudentDocumentsView: View {
    var model: AppModel
    @State private var reports: [AlmaDocumentOption] = []
    @State private var isLoading = false
    @State private var error: String?

    var body: some View {
        List {
            Section("Available reports") {
                if !model.hasCredentials {
                    NavigationLink("Connect your university account") {
                        SettingsView(model: model)
                    }
                } else if isLoading {
                    ProgressView("Checking Alma")
                } else if let error {
                    StatusBanner(title: "Could not check reports", message: error, systemImage: "exclamationmark.triangle")
                    Button("Check again") { Task { await load() } }
                } else if reports.isEmpty {
                    Text("Alma did not list any reports.").foregroundStyle(.secondary)
                } else {
                    ForEach(reports) { report in
                        NavigationLink(report.title) {
                            StudentDocumentDetail(model: model, report: report)
                        }
                    }
                }
            }

            Section("Official portal") {
                Link(destination: AlmaDocumentSession.officialURL) {
                    Label("Open Study Service in Alma", systemImage: "arrow.up.right")
                }
            }
        }
        .navigationTitle("Documents")
        .task(id: model.hasCredentials) { await load() }
        .refreshable { await load() }
    }

    private func load() async {
        reports = []
        error = nil
        guard model.hasCredentials else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let (client, credentials) = try model.almaAccessContext(for: "check available reports")
            let result = try await AlmaDocumentSession(client: client).reports(credentials: credentials)
            try Task.checkCancellation()
            reports = result
        } catch is CancellationError {
            return
        } catch {
            self.error = error.localizedDescription
        }
    }
}

private struct StudentDocumentDetail: View {
    var model: AppModel
    let report: AlmaDocumentOption
    @State private var session: AlmaDocumentSession?
    @State private var prepared: AlmaPreparedDocument?
    @State private var term: AlmaDocumentOption?
    @State private var pdf: PDFDocument?
    @State private var file: StudentPDF?
    @State private var isLoading = false
    @State private var error: String?

    var body: some View {
        List {
            Section("Official document · Alma") {
                Text(report.title)
                if let prepared, !prepared.terms.isEmpty {
                    Picker("Semester", selection: $term) {
                        Text("Choose a semester").tag(nil as AlmaDocumentOption?)
                        ForEach(prepared.terms) { option in
                            Text(option.title).tag(Optional(option))
                        }
                    }
                    .disabled(isLoading || pdf != nil)
                }
                if isLoading {
                    ProgressView("Requesting PDF from Alma")
                } else if let file {
                    ShareLink(item: file, preview: SharePreview(report.title)) {
                        Label("Share or save PDF", systemImage: "square.and.arrow.up")
                    }
                } else if let error {
                    StatusBanner(title: "Report unavailable", message: error, systemImage: "exclamationmark.triangle")
                    Link("Open Study Service in Alma", destination: AlmaDocumentSession.officialURL)
                } else if let prepared, let session {
                    Button("Download PDF") {
                        Task { await request { try await accept(session.download(prepared, term: term)) } }
                    }
                    .disabled(!prepared.terms.isEmpty && term == nil)
                } else {
                    Button("Prepare report") { Task { await request { try await prepare() } } }
                }
            }

            if let pdf {
                Section("PDF preview") {
                    StudentPDFPreview(document: pdf).frame(height: 440)
                }
            }
        }
        .navigationTitle("Report")
        .privacySensitive()
    }

    private func prepare() async throws {
        let (client, credentials) = try model.almaAccessContext(for: "prepare this report")
        let session = AlmaDocumentSession(client: client)
        switch try await session.prepare(report, credentials: credentials) {
        case .ready(let data):
            try accept(data)
        case .choose(let preparation):
            self.session = session
            self.prepared = preparation
        }
    }

    private func accept(_ data: Data) throws {
        guard let document = PDFDocument(data: data), document.pageCount > 0 else {
            throw AlmaDocumentError.unavailable("The document returned by Alma could not be opened.")
        }
        pdf = document
        file = StudentPDF(data: data)
    }

    private func request(_ action: () async throws -> Void) async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }
        do { try await action() }
        catch { self.error = error.localizedDescription }
    }
}

private struct StudentPDF: Transferable {
    let data: Data

    static var transferRepresentation: some TransferRepresentation {
        DataRepresentation(exportedContentType: .pdf) { $0.data }
            .suggestedFileName("Alma report")
    }
}

private struct StudentPDFPreview: UIViewRepresentable {
    let document: PDFDocument

    func makeUIView(context: Context) -> PDFView {
        let view = PDFView()
        view.autoScales = true
        return view
    }

    func updateUIView(_ view: PDFView, context: Context) {
        view.document = document
    }
}
