import 'package:collection/collection.dart';
import 'package:education_planner/extensions/x_path_subject_list.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:planner_repository/planner_repository.dart';

class PlannerModifyView extends StatefulWidget {
  const PlannerModifyView({super.key});

  static void show(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (_) {
        return Dialog.fullscreen(
          child: MultiBlocProvider(
            providers: [
              BlocProvider.value(
                value: context.read<SchoolingBloc>(),
              ),
              BlocProvider.value(
                value: context.read<PlannerBloc>(),
              ),
            ],
            child: const PlannerModifyView(),
          ),
        );
      },
    );
  }

  @override
  State<PlannerModifyView> createState() => _PlannerModifyViewState();
}

class _PlannerModifyViewState extends State<PlannerModifyView> {
  late GlobalKey<ScaffoldState> _scaffoldKey;

  @override
  void initState() {
    super.initState();
    _scaffoldKey = GlobalKey<ScaffoldState>();
  }

  @override
  Widget build(BuildContext context) {
    final plan = context.select(
      (PlannerBloc bloc) => bloc.state.modifiedDegreePlan,
    );

    return BlocListener<PlannerBloc, PlannerState>(
      listenWhen: (previous, current) =>
          previous.drawerStatus != current.drawerStatus ||
          previous.status != current.status,
      listener: (context, state) async {
        if (state.drawerStatus == PlannerDrawerStatus.opened) {
          _scaffoldKey.currentState?.openEndDrawer();
        } else {
          _scaffoldKey.currentState?.closeEndDrawer();
        }
      },
      child: Scaffold(
        key: _scaffoldKey,
        appBar: AppBar(
          actions: const [SizedBox.shrink()],
        ),
        onEndDrawerChanged: (open) {
          if (!open) {
            _scaffoldKey.currentState?.closeEndDrawer();
            context.read<PlannerBloc>().add(
                  const PlannerDrawerChanged(),
                );
          }
        },
        endDrawer: const _SubjectsDrawer(),
        body: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _ButtonPanel(),
            Expanded(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      StudentPlan(
                        plan: plan,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SubjectsDrawer extends StatelessWidget {
  const _SubjectsDrawer();

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width * 0.5;

    return Drawer(
      width: width,
      child: Scaffold(
        appBar: AppBar(),
        bottomNavigationBar: BottomAppBar(
          child: SizedBox(
            width: 100,
            child: OutlinedButton(
              onPressed: () {
                Navigator.of(context).pop();
                context.read<PlannerBloc>().add(
                      const PlannerSubjectsSubmitted(),
                    );
              },
              child: const Text('Agregar'),
            ),
          ),
        ),
        body: const Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 4),
                child: Text(
                  'Escoge las materias a agregar para el semestre',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              SizedBox(height: 20),
              _SubjectsSelection(),
            ],
          ),
        ),
      ),
    );
  }
}

class _SubjectsSelection extends StatelessWidget {
  const _SubjectsSelection();

  @override
  Widget build(BuildContext context) {
    final schooling = context.select(
      (SchoolingBloc bloc) => bloc.state.schooling,
    );
    final schoolingSubjects =
        schooling?.subjects.where((subject) => subject.isApproved).toList() ??
            [];
    final degreePlanSubjects = context
        .select((PlannerBloc bloc) => bloc.state.subjects)
        .whereNot(
          (subject) =>
              subject.name.contains('Electiva') ||
              subject.subjectIds.isNotEmpty,
        )
        .toList();
    final modifiedDegreePlanSubjects = context
        .select((PlannerBloc bloc) => bloc.state.modifiedDegreePlan)
        .map((s) => s.semesters.expand((p) => p.subjects).toList())
        .expand(
          (s) => s,
        )
        .toList();

    final subjects = degreePlanSubjects.filterNotApprovedSubjects(
      schoolingSubjects: schoolingSubjects,
      modifiedDegreePlanSubjects: modifiedDegreePlanSubjects,
    );

    return Wrap(
      children: [
        ...subjects.map((subject) {
          return Padding(
            padding: const EdgeInsets.all(4),
            child: ChoiceChip(
              label: Text(subject.name),
              selected: context.select(
                (PlannerBloc bloc) =>
                    bloc.state.selectedSubjects
                        .firstWhereOrNull((s) => s.id == subject.id) !=
                    null,
              ),
              padding: const EdgeInsets.all(8),
              onSelected: (_) {
                context.read<PlannerBloc>().add(
                      PlannerSubjectSelected(
                        subject: PathSubject(
                          id: subject.id,
                          name: subject.name,
                        ),
                      ),
                    );
              },
            ),
          );
        }),
      ],
    );
  }
}

class _ButtonPanel extends StatelessWidget {
  const _ButtonPanel();

  @override
  Widget build(BuildContext context) {
    final semesterRecommendationPerformed = context.select(
      (PlannerBloc bloc) => bloc.state.semesterRecommendationPerformed,
    );

    final schooling = context.select(
      (SchoolingBloc bloc) => bloc.state.schooling,
    );
    final schoolingSubjects =
        schooling?.subjects.where((subject) => subject.isApproved).toList() ??
            [];
    final degreePlanSubjects = context
        .select((PlannerBloc bloc) => bloc.state.subjects)
        .whereNot(
          (subject) =>
              subject.name.contains('Electiva') ||
              subject.subjectIds.isNotEmpty,
        )
        .toList();
    final modifiedDegreePlanSubjects = context
        .select((PlannerBloc bloc) => bloc.state.modifiedDegreePlan)
        .map((s) => s.semesters.expand((p) => p.subjects).toList())
        .expand(
          (s) => s,
        )
        .toList();

    final subjects = degreePlanSubjects.filterNotApprovedSubjects(
      schoolingSubjects: schoolingSubjects,
      modifiedDegreePlanSubjects: modifiedDegreePlanSubjects,
    );
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).colorScheme.outline.withAlpha(20),
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Planificador de estudios',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Text(
                'Modifica tu plan de estudios',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(),
              ),
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              _ActionButton(
                icon: Icons.add,
                label: 'Agregar semestre',
                onPressed: () {
                  context.read<PlannerBloc>().add(
                        const PlannerDrawerChanged(),
                      );
                },
              ),
              const SizedBox(width: 8),
              if (!semesterRecommendationPerformed)
                _ActionButton(
                  icon: Icons.auto_awesome,
                  label: 'Recomendar asignaturas',
                  onPressed: () {
                    final degreePlan =
                        context.read<PlannerBloc>().state.modifiedDegreePlan;
                    context.read<PlannerBloc>().add(
                          PlannerSubjectRecomendationsForSemesterFetched(
                            semester: degreePlan.last.semesters.last,
                          ),
                        );
                  },
                ),
              const SizedBox(width: 8),
              _ActionButton(
                icon: Icons.analytics,
                label: 'Analizar asignaturas',
                onPressed: () {
                  SubjectAnalysisPopup.show(
                    context,
                    subjects: subjects,
                    onAnalyze: (subject) {
                      context.read<PlannerBloc>().add(
                            PlannerSubjectAnalysisRequested(
                              subject: subject,
                            ),
                          );
                    },
                  );
                },
              ),
              const SizedBox(width: 8),
              _ActionButton(
                icon: Icons.save,
                label: 'Guardar',
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Plan guardado exitosamente'),
                    ),
                  );
                },
                isPrimary: true,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.isPrimary = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final bool isPrimary;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(
        icon,
        size: 18,
        color: isPrimary
            ? Theme.of(context).colorScheme.onPrimary
            : Theme.of(context).colorScheme.onSurface,
      ),
      label: Text(
        label,
        style: const TextStyle(fontSize: 12),
        textAlign: TextAlign.center,
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: isPrimary
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).colorScheme.surface,
        foregroundColor: isPrimary
            ? Theme.of(context).colorScheme.onPrimary
            : Theme.of(context).colorScheme.onSurface,
        elevation: isPrimary ? 2 : 1,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        maximumSize: const Size(400, 40),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(6),
          side: BorderSide(
            color: isPrimary
                ? Theme.of(context).colorScheme.primary
                : Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
          ),
        ),
      ),
    );
  }
}
