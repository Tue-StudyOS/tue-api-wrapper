import 'package:flutter/material.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({
    required this.username,
    required this.password,
    required this.busy,
    required this.error,
    required this.onSignIn,
    super.key,
  });

  final TextEditingController username;
  final TextEditingController password;
  final bool busy;
  final String? error;
  final VoidCallback onSignIn;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
          children: [
            Icon(Icons.school_outlined,
                size: 44, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 18),
            Text('Study Hub',
                style: Theme.of(context)
                    .textTheme
                    .headlineMedium
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(
              'Sign in once to load your Alma timetable, Moodle deadlines, ILIAS tasks, and grades on this device.',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),
            DecoratedBox(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    TextField(
                        controller: username,
                        textInputAction: TextInputAction.next,
                        decoration:
                            const InputDecoration(labelText: 'ZDV user')),
                    const SizedBox(height: 12),
                    TextField(
                      controller: password,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Password'),
                      onSubmitted: (_) {
                        if (!busy) {
                          onSignIn();
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: busy ? null : onSignIn,
                      icon: busy
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.login),
                      label: const Text('Sign in'),
                      style: FilledButton.styleFrom(
                          minimumSize: const Size.fromHeight(48)),
                    ),
                  ],
                ),
              ),
            ),
            if (error != null) ...[
              const SizedBox(height: 16),
              Text(error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
          ],
        ),
      ),
    );
  }
}
