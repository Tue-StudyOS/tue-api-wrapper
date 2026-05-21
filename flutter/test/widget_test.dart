import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:tue_api_flutter/src/ui/app.dart';

void main() {
  testWidgets('renders login shell without credentials',
      (WidgetTester tester) async {
    FlutterSecureStorage.setMockInitialValues({});
    await tester.pumpWidget(const TueApiFlutterApp());
    await tester.pump();
    await tester.pump();

    expect(find.text('Study Hub'), findsOneWidget);
    expect(find.text('ZDV user'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
