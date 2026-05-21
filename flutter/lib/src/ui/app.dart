import 'package:flutter/material.dart';

import 'dashboard_screen.dart';

class TueApiFlutterApp extends StatelessWidget {
  const TueApiFlutterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TUE Study',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff0a7c78)),
        scaffoldBackgroundColor: const Color(0xfff4f5f7),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xfff4f5f7),
          elevation: 0,
          centerTitle: true,
        ),
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Color(0xffffffff),
          height: 72,
        ),
        inputDecorationTheme:
            const InputDecorationTheme(border: OutlineInputBorder()),
      ),
      home: const DashboardScreen(),
    );
  }
}
