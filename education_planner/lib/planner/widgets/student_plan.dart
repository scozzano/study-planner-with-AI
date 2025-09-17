import 'package:collection/collection.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:shimmer/shimmer.dart';

class StudentPlan extends StatefulWidget {
  const StudentPlan({
    required this.plan,
    this.editablePlan,
    super.key,
  });
  final List<DegreeYear> plan;
  final Widget? editablePlan;

  @override
  State<StudentPlan> createState() => _StudentPlanState();
}

class _StudentPlanState extends State<StudentPlan> {
  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: _StudentPlanBody(
          plan: widget.plan,
          editablePlan: widget.editablePlan,
        ),
      ),
    );
  }
}

class _StudentPlanBody extends StatelessWidget {
  const _StudentPlanBody({
    required this.plan,
    this.editablePlan,
  });

  final List<DegreeYear> plan;
  final Widget? editablePlan;

  @override
  Widget build(BuildContext context) {
    final schoolingStatus = context.select(
      (SchoolingBloc bloc) => bloc.state.status,
    );
    final plannerStatus = context.select(
      (PlannerBloc bloc) => bloc.state.status,
    );

    final content = SingleChildScrollView(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...plan.mapIndexed((index, degreePlan) {
            return Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Column(
                children: [
                  _YearCard(degreePlan: degreePlan),
                  const SizedBox(height: 8),
                  _SemesterColumn(degreePlan: degreePlan),
                ],
              ),
            );
          }),
          if (editablePlan != null) editablePlan!,
        ],
      ),
    );

    if (plannerStatus == PlannerStatus.fetchingRecommendations ||
        schoolingStatus.isLoading ||
        plan.isEmpty) {
      return Shimmer.fromColors(
        baseColor: Colors.grey[300]!,
        highlightColor: Colors.grey[100]!,
        child: content,
      );
    }
    return content;
  }
}

class _YearCard extends StatelessWidget {
  const _YearCard({
    required this.degreePlan,
  });

  final DegreeYear degreePlan;

  @override
  Widget build(BuildContext context) {
    final semesters = degreePlan.semesters.length;

    return Card(
      color: Theme.of(context).colorScheme.secondary,
      child: Container(
        width: (150 * semesters).toDouble(),
        padding: const EdgeInsets.all(4),
        child: Center(
          child: Text(
            degreePlan.year.toString(),
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSecondary,
                ),
          ),
        ),
      ),
    );
  }
}

class _SemesterColumn extends StatelessWidget {
  const _SemesterColumn({
    required this.degreePlan,
  });

  final DegreeYear degreePlan;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: degreePlan.semesters.map((semester) {
          return DragTarget<SelectedSemester>(
            onLeave: (data) {
              if (degreePlan.containsEditableSemester() &&
                  data != null &&
                  data.subjects.any(
                    (subject) => data.semester.subjects.contains(subject),
                  )) {
                context.read<PlannerBloc>().add(
                      PlannerSubjectRemoved(updatedSemester: data),
                    );
              }
            },
            onAcceptWithDetails: (DragTargetDetails<SelectedSemester> details) {
              final data = details.data;
              if (!data.subjects
                  .any((subject) => semester.subjects.contains(subject))) {
                final selectedSemester = data;
                final newSemester = SelectedSemester(
                  semester: semester,
                  subjects: selectedSemester.subjects,
                );

                context.read<PlannerBloc>().add(
                      PlannerSubjectChanged(updatedSemester: newSemester),
                    );
              }
            },
            onWillAcceptWithDetails:
                (DragTargetDetails<SelectedSemester> details) {
              return degreePlan.containsEditableSemester();
            },
            builder: (context, candidateData, rejectedData) {
              return Column(
                children: [
                  _SemesterTitle(semester: semester),
                  const SizedBox(height: 8),
                  if (semester.subjects.isEmpty) ...[
                    _EmptyCard(semester),
                  ],
                  if (semester.subjects.isNotEmpty)
                    ...semester.subjects.map((subject) {
                      return semester.isEditable
                          ? Draggable<SelectedSemester>(
                              data: SelectedSemester(
                                semester: semester,
                                subjects: [subject],
                              ),
                              onDraggableCanceled: (velocity, offset) {
                                context.read<PlannerBloc>().add(
                                      PlannerSubjectChanged(
                                        updatedSemester: SelectedSemester(
                                          semester: semester,
                                          subjects: [subject],
                                        ),
                                      ),
                                    );
                              },
                              feedback: PlanCard(subject: subject),
                              child: PlanCard(subject: subject),
                            )
                          : PlanCard(subject: subject);
                    }),
                  if (semester.subjects.isNotEmpty && degreePlan.isEditable)
                    _EmptyCard(semester),
                ],
              );
            },
          );
        }).toList(),
      ),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard(
    this.semester,
  );

  final Semester semester;

  @override
  Widget build(BuildContext context) {
    final isLoading = context.select(
      (PlannerBloc bloc) => bloc.state.status == PlannerStatus.loading,
    );
    if (isLoading) {
      return const SizedBox.shrink();
    }
    return Card.outlined(
      child: InkWell(
        onTap: () {
          context.read<PlannerBloc>().add(
                PlannerDrawerChanged(
                  semesterTarget: semester,
                ),
              );
        },
        child: const SizedBox(
          height: 100,
          width: 150,
          child: Center(child: Icon(Icons.add)),
        ),
      ),
    );
  }
}

class _SemesterTitle extends StatelessWidget {
  const _SemesterTitle({
    required this.semester,
  });
  final Semester semester;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.tertiaryContainer,
      child: SizedBox(
        width: 150,
        child: Center(
          child: Text('Semestre ${semester.semester}'),
        ),
      ),
    );
  }
}

class SelectedSemester extends Equatable {
  const SelectedSemester({
    required this.semester,
    required this.subjects,
  });

  final Semester semester;
  final List<PathSubject> subjects;

  @override
  List<Object> get props => [semester, subjects];
}
