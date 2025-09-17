import 'package:education_planner/constants.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

class PlannerPage extends Page<void> {
  const PlannerPage();
  static const path = '/planner';

  @override
  Route<void> createRoute(BuildContext context) {
    return MaterialPageRoute(
      fullscreenDialog: true,
      settings: this,
      builder: (ctx) {
        return BlocProvider(
          create: (context) => PlannerBloc(
            plannerRepository: context.read<PlannerRepository>(),
            studentRepository: context.read<StudentRepository>(),
          )..add(
              const PlannerDegreePathRequested(
                degreeId: Constants.kSystemsDegreeId,
              ),
            ),
          child: const PlannerView(),
        );
      },
    );
  }
}
