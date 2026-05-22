import AVFoundation
import SwiftUI

struct KufBarcodeScanResult: Equatable {
    var value: String
    var symbology: String
}

struct KufBarcodeScannerView: UIViewControllerRepresentable {
    var onScan: (KufBarcodeScanResult) -> Void
    var onError: (String) -> Void
    var preferredMetadataTypes: [AVMetadataObject.ObjectType] = Self.defaultPreferredMetadataTypes
    var cameraDeniedMessage = "Camera access is needed to scan the KuF barcode."

    func makeUIViewController(context: Context) -> KufBarcodeScannerViewController {
        KufBarcodeScannerViewController(
            preferredMetadataTypes: preferredMetadataTypes,
            cameraDeniedMessage: cameraDeniedMessage,
            onScan: onScan,
            onError: onError
        )
    }

    func updateUIViewController(
        _ uiViewController: KufBarcodeScannerViewController,
        context: Context
    ) {}

    static let defaultPreferredMetadataTypes: [AVMetadataObject.ObjectType] = [
        .ean13,
        .ean8,
        .code128,
        .code39,
        .code39Mod43,
        .interleaved2of5,
        .itf14,
        .qr,
        .pdf417,
        .aztec
    ]
}

final class KufBarcodeScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    private let session = AVCaptureSession()
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var didScan = false
    private let preferredMetadataTypes: [AVMetadataObject.ObjectType]
    private let cameraDeniedMessage: String
    private let onScan: (KufBarcodeScanResult) -> Void
    private let onError: (String) -> Void

    init(
        preferredMetadataTypes: [AVMetadataObject.ObjectType],
        cameraDeniedMessage: String,
        onScan: @escaping (KufBarcodeScanResult) -> Void,
        onError: @escaping (String) -> Void
    ) {
        self.preferredMetadataTypes = preferredMetadataTypes
        self.cameraDeniedMessage = cameraDeniedMessage
        self.onScan = onScan
        self.onError = onError
        super.init(nibName: nil, bundle: nil)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        requestCameraAccess()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.bounds
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        stopSession()
    }

    func metadataOutput(
        _ output: AVCaptureMetadataOutput,
        didOutput metadataObjects: [AVMetadataObject],
        from connection: AVCaptureConnection
    ) {
        guard !didScan else { return }
        guard let codeObject = metadataObjects.compactMap({ $0 as? AVMetadataMachineReadableCodeObject }).first,
              let value = codeObject.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !value.isEmpty else {
            return
        }

        didScan = true
        stopSession()
        onScan(KufBarcodeScanResult(value: value, symbology: codeObject.type.rawValue))
    }

    private func requestCameraAccess() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            configureSession()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    granted ? self?.configureSession() : self?.reportCameraDenied()
                }
            }
        case .denied, .restricted:
            reportCameraDenied()
        @unknown default:
            reportCameraDenied()
        }
    }

    private func configureSession() {
        do {
            guard let device = AVCaptureDevice.default(for: .video) else {
                onError("No camera is available on this device.")
                return
            }

            let input = try AVCaptureDeviceInput(device: device)
            guard session.canAddInput(input) else {
                onError("The camera could not be attached.")
                return
            }
            session.addInput(input)

            let output = AVCaptureMetadataOutput()
            guard session.canAddOutput(output) else {
                onError("Barcode scanning is not available.")
                return
            }
            session.addOutput(output)
            output.setMetadataObjectsDelegate(self, queue: .main)
            let metadataTypes = supportedMetadataTypes(from: output.availableMetadataObjectTypes)
            guard !metadataTypes.isEmpty else {
                onError("This device does not report any supported barcode scanner formats.")
                return
            }
            output.metadataObjectTypes = metadataTypes

            let previewLayer = AVCaptureVideoPreviewLayer(session: session)
            previewLayer.videoGravity = .resizeAspectFill
            previewLayer.frame = view.bounds
            view.layer.insertSublayer(previewLayer, at: 0)
            self.previewLayer = previewLayer

            DispatchQueue.global(qos: .userInitiated).async { [session] in
                session.startRunning()
            }
        } catch {
            onError(error.localizedDescription)
        }
    }

    private func supportedMetadataTypes(
        from availableTypes: [AVMetadataObject.ObjectType]
    ) -> [AVMetadataObject.ObjectType] {
        preferredMetadataTypes.filter(availableTypes.contains)
    }

    private func stopSession() {
        guard session.isRunning else { return }
        DispatchQueue.global(qos: .userInitiated).async { [session] in
            session.stopRunning()
        }
    }

    private func reportCameraDenied() {
        onError(cameraDeniedMessage)
    }
}
