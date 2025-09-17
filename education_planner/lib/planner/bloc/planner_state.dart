part of 'planner_bloc.dart';

enum PlannerStatus {
  initial,
  loading,
  loaded,
  error,
  fetchingRecommendations,
  fetchingDTRecommendations,
}

enum PlannerDrawerStatus {
  closed,
  opened,
}

class PlannerState extends Equatable {
  const PlannerState({
    required this.status,
    required this.subjects,
    required this.drawerStatus,
    required this.selectedSubjects,
    required this.degreePlan,
    required this.modifiedDegreePlan,
    required this.semesterRecommendationPerformed,
    required this.semesterTarget,
    required this.recommendedRuleSubjects,
    required this.ruleSuggestions,
    required this.csRecommendations,
    required this.allPathSubjects,
  });

  const PlannerState.initial()
      : status = PlannerStatus.initial,
        subjects = const [],
        drawerStatus = PlannerDrawerStatus.closed,
        selectedSubjects = const [],
        degreePlan = const [],
        modifiedDegreePlan = const [],
        semesterRecommendationPerformed = false,
        semesterTarget = const Semester.empty(),
        recommendedRuleSubjects = const [],
        ruleSuggestions = const [],
        csRecommendations = const [],
        allPathSubjects = const [];

  final PlannerStatus status;
  final List<PathSubject> subjects;
  final PlannerDrawerStatus drawerStatus;
  final List<PathSubject> selectedSubjects;
  final List<DegreeYear> degreePlan;
  final List<DegreeYear> modifiedDegreePlan;
  final bool semesterRecommendationPerformed;
  final Semester semesterTarget;
  final List<String> recommendedRuleSubjects;
  final List<RuleSuggestion> ruleSuggestions;
  final List<SuccessRecommendation> csRecommendations;
  final List<PathSubject> allPathSubjects;

  List<RuleSuggestion> get displayableRuleSuggestions =>
      ruleSuggestions.where((s) => s.shouldDisplay).toList();

  PlannerState copyWith({
    PlannerStatus? status,
    List<PathSubject>? subjects,
    PlannerDrawerStatus? drawerStatus,
    List<PathSubject>? selectedSubjects,
    List<DegreeYear>? degreePlan,
    List<DegreeYear>? modifiedDegreePlan,
    bool? semesterRecommendationPerformed,
    Semester? semesterTarget,
    List<String>? recommendedRuleSubjects,
    List<RuleSuggestion>? ruleSuggestions,
    List<SuccessRecommendation>? csRecommendations,
    List<PathSubject>? allPathSubjects,
  }) {
    return PlannerState(
      status: status ?? this.status,
      subjects: subjects ?? this.subjects,
      drawerStatus: drawerStatus ?? this.drawerStatus,
      selectedSubjects: selectedSubjects ?? this.selectedSubjects,
      degreePlan: degreePlan ?? this.degreePlan,
      modifiedDegreePlan: modifiedDegreePlan ?? this.modifiedDegreePlan,
      semesterRecommendationPerformed: semesterRecommendationPerformed ??
          this.semesterRecommendationPerformed,
      semesterTarget: semesterTarget ?? this.semesterTarget,
      recommendedRuleSubjects:
          recommendedRuleSubjects ?? this.recommendedRuleSubjects,
      ruleSuggestions: ruleSuggestions ?? this.ruleSuggestions,
      csRecommendations: csRecommendations ?? this.csRecommendations,
      allPathSubjects: allPathSubjects ?? this.allPathSubjects,
    );
  }

  @override
  List<Object?> get props => [
        status,
        subjects,
        drawerStatus,
        selectedSubjects,
        degreePlan,
        modifiedDegreePlan,
        semesterRecommendationPerformed,
        semesterTarget,
        recommendedRuleSubjects,
        ruleSuggestions,
        csRecommendations,
        allPathSubjects,
      ];
}
