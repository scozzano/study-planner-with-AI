import 'package:education_planner/onboarding/onboarding.dart';
import 'package:flutter/material.dart';

class OnboardingPage extends Page<void> {
  const OnboardingPage();
  static const path = '/onboarding';

  @override
  Route<void> createRoute(BuildContext context) {
    return MaterialPageRoute(
      fullscreenDialog: true,
      settings: this,
      builder: (ctx) {
        return const OnboardingView();
      },
    );
  }
}
