import 'package:education_planner/app/app.dart';
import 'package:education_planner/app/bloc/app_bloc.dart';
import 'package:education_planner/l10n/l10n.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

class App extends StatelessWidget {
  const App({
    required StudentRepository studentRepository,
    required PlannerRepository plannerRepository,
    super.key,
  })  : _studentRepository = studentRepository,
        _plannerRepository = plannerRepository;

  final StudentRepository _studentRepository;
  final PlannerRepository _plannerRepository;

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider.value(
          value: _studentRepository,
        ),
        RepositoryProvider.value(
          value: _plannerRepository,
        ),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider(
            create: (context) => AppBloc()..add(AppStudentIdLoaded()),
          ),
          BlocProvider(
            create: (context) => SchoolingBloc(
              studentRepository: context.read<StudentRepository>(),
            )..add(const SchoolingFetched()),
          ),
        ],
        child: const _AppView(),
      ),
    );
  }
}

class _AppView extends StatelessWidget {
  const _AppView();

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      theme: ThemeData(
        colorScheme: const ColorScheme(
          brightness: Brightness.light,
          primary: Color(0xFF1B365D),
          onPrimary: Color(0xFFFFFFFF),
          primaryContainer: Color.fromARGB(255, 135, 174, 200),
          onPrimaryContainer: Color(0xFF001B3D),
          secondary: Color(0xFF0F4C75),
          onSecondary: Color(0xFFFFFFFF),
          secondaryContainer: Color(0xFFCCE5FF),
          onSecondaryContainer: Color(0xFF001E3C),
          tertiary: Color(0xFF00695C),
          onTertiary: Color(0xFFFFFFFF),
          tertiaryContainer: Color(0xFFE0F2F1),
          onTertiaryContainer: Color(0xFF00201C),
          error: Color(0xFFBA1A1A),
          onError: Color(0xFFFFFFFF),
          errorContainer: Color(0xFFFFDAD6),
          onErrorContainer: Color(0xFF410002),
          surface: Color(0xFFFFFFFF),
          onSurface: Color(0xFF000000),
          surfaceContainerHighest: Color(0xFFE0E2EC),
          onSurfaceVariant: Color(0xFF43474E),
          outline: Color(0xFF73777F),
          outlineVariant: Color(0xFFC3C7CF),
          shadow: Color(0xFF000000),
          scrim: Color(0xFF000000),
          inverseSurface: Color(0xFF2F3033),
          onInverseSurface: Color(0xFFF0F0F3),
          inversePrimary: Color(0xFF9FCCFF),
          surfaceTint: Color(0xFF1B365D),
        ),
        textTheme: GoogleFonts.interTextTheme(),
        useMaterial3: true,
      ),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      debugShowCheckedModeBanner: false,
      routerConfig: AppRouter.router(
        appBloc: context.read<AppBloc>(),
      ),
      builder: (context, child) {
        return child ?? const SizedBox.shrink();
      },
    );
  }
}
