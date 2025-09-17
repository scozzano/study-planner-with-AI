import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class PlannerView extends StatelessWidget {
  const PlannerView({super.key});

  @override
  Widget build(BuildContext context) {
    final status = context.select(
      (PlannerBloc bloc) => bloc.state.status,
    );

    return Scaffold(
      body: DefaultTabController(
        length: 2,
        child: Column(
          children: [
            const TabBar(
              physics: NeverScrollableScrollPhysics(),
              tabs: [
                Tab(text: 'Mi plan'),
                Tab(text: 'Plan sugerido por la universidad'),
              ],
            ),
            Expanded(
              child: TabBarView(
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  const _StudentPlanLayout(),
                  if (status == PlannerStatus.loading)
                    const Center(child: CircularProgressIndicator())
                  else
                    const _DegreePlan(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StudentPlanLayout extends StatelessWidget {
  const _StudentPlanLayout();

  @override
  Widget build(BuildContext context) {
    final schooling = context.select(
      (SchoolingBloc bloc) => bloc.state.schooling,
    );
    if (schooling == null) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }
    final plan = buildStudentDegreePlan(schooling: schooling);

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.edit_outlined),
        onPressed: () {
          PlannerModifyView.show(context);
        },
      ),
      body: StudentPlan(
        plan: plan,
      ),
    );
  }
}

class _DegreePlan extends StatelessWidget {
  const _DegreePlan();

  @override
  Widget build(BuildContext context) {
    final subjects = context.select(
      (PlannerBloc bloc) => bloc.state.subjects,
    );
    final approvedSubjects = context
            .select(
              (SchoolingBloc bloc) => bloc.state.schooling?.subjects.where(
                (subject) => subject.isApproved,
              ),
            )
            ?.toList() ??
        [];
    final plan = buildDegreePlan(subjects, approvedSubjects);

    return Container(
      padding: const EdgeInsets.all(20),
      child: ListView(
        scrollDirection: Axis.horizontal,
        shrinkWrap: true,
        children: [
          ...plan.map((degreePlan) {
            return Column(
              children: [
                Card(
                  color: Theme.of(context).colorScheme.secondary,
                  child: Container(
                    width: (150 * degreePlan.semesters.length).toDouble(),
                    padding: const EdgeInsets.all(4),
                    child: Center(
                      child: Text(
                        'Año ${degreePlan.year}',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              color: Theme.of(context).colorScheme.onSecondary,
                            ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                _SemesterColumn(degreePlan: degreePlan),
              ],
            );
          }),
        ],
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
          return Column(
            children: [
              Card(
                color: Theme.of(context).colorScheme.tertiaryContainer,
                child: SizedBox(
                  width: 150,
                  child: Center(child: Text('Semestre ${semester.semester}')),
                ),
              ),
              const SizedBox(height: 8),
              ...semester.subjects.map((subject) {
                return PlanCard(subject: subject);
              }),
            ],
          );
        }).toList(),
      ),
    );
  }
}
