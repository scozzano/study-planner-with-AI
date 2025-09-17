import 'package:education_planner/app/bloc/app_bloc.dart';
import 'package:education_planner/app/widgets/condensed_drawer.dart';
import 'package:education_planner/onboarding/onboarding.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

final rootNavigatorKey = GlobalKey<NavigatorState>();

class AppRouter {
  /// Only routes that are accessible to unauthenticated users
  static const onlyUnauthenticatedUserRoutes = <String>[OnboardingPage.path];

  /// Only routes that are accessible for authenticated users
  static const onlyAuthenticatedUserRoutes = <String>[
    PlannerPage.path,
    SchoolingPage.path,
  ];

  static GoRouter router({required AppBloc appBloc}) {
    return GoRouter(
      navigatorKey: rootNavigatorKey,
      initialLocation: OnboardingPage.path,
      refreshListenable: appBloc.state.studentIdNotifier,
      redirect: (context, state) {
        final path = state.uri.path;
        final notifier = appBloc.state.studentIdNotifier;
        if (onlyUnauthenticatedUserRoutes.contains(path) &&
            notifier.value.isNotEmpty) {
          return PlannerPage.path;
        }
        if (notifier.value.isEmpty) {
          return OnboardingPage.path;
        }

        return null;
      },
      routes: [
        GoRoute(
          path: OnboardingPage.path,
          pageBuilder: (context, state) {
            return const OnboardingPage();
          },
        ),
        ShellRoute(
          builder: (context, state, child) {
            return Scaffold(
              body: Row(
                children: [
                  const CondensedDrawer(),
                  Expanded(child: child),
                ],
              ),
            );
          },
          routes: [
            GoRoute(
              path: SchoolingPage.path,
              pageBuilder: (context, state) {
                return const SchoolingPage();
              },
            ),
            GoRoute(
              path: PlannerPage.path,
              pageBuilder: (context, state) {
                return const PlannerPage();
              },
            ),
          ],
        ),
      ],
    );
  }
}
