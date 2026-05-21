import 'package:flutter/material.dart';

import 'app_section.dart';

class CredentialsPanel extends StatelessWidget {
  const CredentialsPanel({
    required this.username,
    required this.password,
    required this.busy,
    required this.onSave,
    required this.onLoadPrivate,
    super.key,
  });

  final TextEditingController username;
  final TextEditingController password;
  final bool busy;
  final VoidCallback onSave;
  final VoidCallback onLoadPrivate;

  @override
  Widget build(BuildContext context) {
    return AppSection(
      title: 'University Account',
      icon: Icons.lock_outline,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: username,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'ZDV user'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: password,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Password'),
              onSubmitted: (_) {
                if (!busy) {
                  onLoadPrivate();
                }
              },
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: busy ? null : onSave,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('Save'),
                ),
                const SizedBox(width: 10),
                OutlinedButton.icon(
                  onPressed: busy ? null : onLoadPrivate,
                  icon: const Icon(Icons.login),
                  label: const Text('Load private'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class PublicPanel extends StatelessWidget {
  const PublicPanel({
    required this.date,
    required this.busy,
    required this.onSubmit,
    super.key,
  });

  final TextEditingController date;
  final bool busy;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return AppSection(
      title: 'Discover Public Data',
      icon: Icons.public,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: date,
              onSubmitted: (_) {
                if (!busy) {
                  onSubmit();
                }
              },
              decoration:
                  const InputDecoration(labelText: 'Public lecture date'),
            ),
          ],
        ),
      ),
    );
  }
}
