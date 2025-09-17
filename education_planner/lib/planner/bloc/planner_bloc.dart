import 'dart:async';

import 'package:bloc/bloc.dart';
import 'package:collection/collection.dart';
import 'package:education_planner/app/app.dart';
import 'package:education_planner/constants.dart';
import 'package:education_planner/extensions/x_degree_year_list.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:equatable/equatable.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

part 'planner_event.dart';
part 'planner_state.dart';

class PlannerBloc extends Bloc<PlannerEvent, PlannerState> {
  PlannerBloc({
    required PlannerRepository plannerRepository,
    required StudentRepository studentRepository,
  })  : _plannerRepository = plannerRepository,
        _studentRepository = studentRepository,
        super(const PlannerState.initial()) {
    on<PlannerDegreePathRequested>(_onDegreePathRequested);
    on<PlannerDrawerChanged>(_onPlannerDrawerChanged);
    on<PlannerSubjectSelected>(_onPlannerSubjectSelected);
    on<PlannerSubjectsSubmitted>(_onPlannerSubjectsSubmitted);
    on<PlannerSubjectChanged>(_onPlannerSubjectChanged);
    on<PlannerSubjectRemoved>(_onPlannerSubjectRemoved);
    on<PlannerSubjectRecomendationsForSemesterFetched>(
      _onPlannerSubjectRecommended,
    );
    on<PlannerSubjectAnalysisRequested>(_onPlannerSubjectAnalysisRequested);
  }

  final PlannerRepository _plannerRepository;
  final StudentRepository _studentRepository;

  FutureOr<void> _onDegreePathRequested(
    PlannerDegreePathRequested event,
    Emitter<PlannerState> emit,
  ) async {
    try {
      final degreePath = await _plannerRepository.getDegreePath(event.degreeId);
      final pathSubjects = await _plannerRepository.getPathSubjects();
      emit(
        state.copyWith(
          status: PlannerStatus.loaded,
          subjects: degreePath.subjects,
          allPathSubjects: pathSubjects,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }

    try {
      emit(state.copyWith(status: PlannerStatus.loading));

      final schooling = await _studentRepository.fetchSchooling(
        studentId: await SharedPreferencesHelper.getStudentId() ?? '',
        degreeId: Constants.kSystemsDegreeId,
      );
      var plan = buildStudentDegreePlan(schooling: schooling);

      /// Agregamos el semestre vacio para agregar materias
      plan = plan.addNewSubjectsToPlan(subjects: []);

      emit(
        state.copyWith(
          status: PlannerStatus.loaded,
          degreePlan: plan,
          modifiedDegreePlan: plan,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }
  }

  FutureOr<void> _onPlannerDrawerChanged(
    PlannerDrawerChanged event,
    Emitter<PlannerState> emit,
  ) async {
    emit(
      state.copyWith(
        drawerStatus: state.drawerStatus == PlannerDrawerStatus.closed
            ? PlannerDrawerStatus.opened
            : PlannerDrawerStatus.closed,
        semesterTarget: event.semesterTarget,
      ),
    );
  }

  FutureOr<void> _onPlannerSubjectSelected(
    PlannerSubjectSelected event,
    Emitter<PlannerState> emit,
  ) async {
    final selectedSubjects = List<PathSubject>.from(state.selectedSubjects);
    if (selectedSubjects.contains(event.subject)) {
      selectedSubjects.remove(event.subject);
    } else {
      selectedSubjects.add(event.subject);
    }
    emit(state.copyWith(selectedSubjects: selectedSubjects));
  }

  FutureOr<void> _onPlannerSubjectsSubmitted(
    PlannerSubjectsSubmitted event,
    Emitter<PlannerState> emit,
  ) async {
    var plan = state.modifiedDegreePlan;
    final selectedSubjects = state.selectedSubjects;

    try {
      emit(
        state.copyWith(
          drawerStatus: PlannerDrawerStatus.closed,
        ),
      );

      if (state.semesterTarget.isEmpty) {
        plan = state.modifiedDegreePlan.addNewSubjectsToPlan(
          subjects: selectedSubjects,
        );
      } else {
        plan = state.modifiedDegreePlan.addSubjectToSemester(
          selectedSemester: SelectedSemester(
            semester: state.semesterTarget,
            subjects: selectedSubjects,
          ),
        );
      }

      emit(
        state.copyWith(
          modifiedDegreePlan: plan,
          selectedSubjects: [],
          semesterTarget: const Semester.empty(),
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }

    try {
      final studentId = await SharedPreferencesHelper.getStudentId() ?? '';
      final recommendedProbability =
          await _plannerRepository.getCSRecommendations(
        studentId: int.parse(studentId),
        candidateSubjects:
            selectedSubjects.map((s) => s.id.toString()).toList(),
        degreeId: Constants.kSystemsDegreeId,
      );

      final recommendations = recommendedProbability.recommendations;
      final updatedSelectedSubjects = selectedSubjects.map((s) {
        final recommendation = recommendations
            .firstWhereOrNull((r) => r.subject == s.id.toString());
        if (recommendation == null) return s;
        return s.copyWith(
          successRate: recommendation.pPass,
        );
      }).toList();

      plan = plan.updateSubjects(
        newSubjects: updatedSelectedSubjects,
      );

      emit(
        state.copyWith(
          status: PlannerStatus.loaded,
          drawerStatus: PlannerDrawerStatus.closed,
          modifiedDegreePlan: plan,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }
  }

  FutureOr<void> _onPlannerSubjectChanged(
    PlannerSubjectChanged event,
    Emitter<PlannerState> emit,
  ) async {
    final updatedDegreePlan = state.modifiedDegreePlan.addSubjectToSemester(
      selectedSemester: event.updatedSemester,
    );

    emit(
      state.copyWith(modifiedDegreePlan: updatedDegreePlan),
    );
  }

  FutureOr<void> _onPlannerSubjectRemoved(
    PlannerSubjectRemoved event,
    Emitter<PlannerState> emit,
  ) async {
    final updatedDegreePlan = _removeSubjectFromSemester(
      degreePlan: state.modifiedDegreePlan,
      selectedSemester: event.updatedSemester,
    );

    emit(state.copyWith(modifiedDegreePlan: updatedDegreePlan));
  }

  List<DegreeYear> _removeSubjectFromSemester({
    required List<DegreeYear> degreePlan,
    required SelectedSemester selectedSemester,
  }) {
    final plan = List<DegreeYear>.from(degreePlan);
    final yearToUpdate = plan.findBySemester(selectedSemester.semester);

    if (yearToUpdate == null) return plan;

    final updatedSemester = yearToUpdate.semesters.map((s) {
      if (s.semester == selectedSemester.semester.semester) {
        for (final subject in selectedSemester.subjects) {
          s.subjects.remove(subject);
        }
      }
      return s;
    }).toList();

    final yearUpdated = yearToUpdate.copyWith(semesters: updatedSemester);

    plan
      ..remove(yearToUpdate)
      ..add(yearUpdated)
      ..sort((a, b) => a.year.compareTo(b.year));

    return plan;
  }

  FutureOr<void> _onPlannerSubjectRecommended(
    PlannerSubjectRecomendationsForSemesterFetched event,
    Emitter<PlannerState> emit,
  ) async {
    emit(state.copyWith(status: PlannerStatus.fetchingRecommendations));
    try {
      final studentId = await SharedPreferencesHelper.getStudentId();
      final recommendations = await _plannerRepository.getPMRecommendations(
        studentId: int.parse(studentId ?? '0'),
        degreeId: Constants.kSystemsDegreeId,
      );

      final recommendedSubjectsIds =
          recommendations.recommendations.map((r) => r.subject).toList();

      final recommendedSubjects = state.subjects
          .where((s) => recommendedSubjectsIds.contains(s.id.toString()))
          .map((s) => s.copyWith(isRecommended: true))
          .toList();

      final updatedDegreePlan = state.modifiedDegreePlan.addSubjectToSemester(
        selectedSemester: SelectedSemester(
          semester: event.semester,
          subjects: recommendedSubjects,
        ),
      );

      emit(
        state.copyWith(
          modifiedDegreePlan: updatedDegreePlan,
          status: PlannerStatus.loaded,
          semesterRecommendationPerformed: true,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }
  }

  FutureOr<void> _onPlannerSubjectAnalysisRequested(
    PlannerSubjectAnalysisRequested event,
    Emitter<PlannerState> emit,
  ) async {
    emit(state.copyWith(status: PlannerStatus.fetchingDTRecommendations));
    try {
      final recommendations = await _plannerRepository.getDTRecommendation(
        course: event.subject.id.toString(),
        degreeId: Constants.kSystemsDegreeId,
      );

      final updatedRecommendedRuleSubjects = recommendations
          .expand((r) => r.parsed ?? [])
          .map((item) => item.toString())
          .toList();

      emit(
        state.copyWith(
          recommendedRuleSubjects: updatedRecommendedRuleSubjects,
          status: PlannerStatus.loaded,
        ),
      );
    } catch (e) {
      emit(state.copyWith(status: PlannerStatus.error));
    }
  }
}
