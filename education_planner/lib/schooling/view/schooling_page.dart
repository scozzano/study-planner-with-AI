import 'package:education_planner/schooling/view/schooling_view.dart';
import 'package:flutter/material.dart';

class SchoolingPage extends Page<void> {
  const SchoolingPage();
  static const path = '/schooling';

  @override
  Route<void> createRoute(BuildContext context) {
    return MaterialPageRoute(
      fullscreenDialog: true,
      settings: this,
      builder: (ctx) {
        return const SchoolingView();
      },
    );
  }
}
