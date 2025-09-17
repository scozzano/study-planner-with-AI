import 'package:education_planner/planner/models/degree_year.dart';
import 'package:equatable/equatable.dart';
import 'package:planner_repository/planner_repository.dart';

/// Enum representing different types of rule conditions
enum RuleType {
  gradeBased,
  actionBased,
}

/// Class representing a processed rule suggestion for the user
class RuleSuggestion extends Equatable {
  const RuleSuggestion({
    required this.subject,
    required this.message,
    required this.accuracy,
    required this.ruleType,
    required this.priority,
    this.relatedSubject,
    this.suggestedSemester,
    this.accepted = false,
    this.read = false,
  });

  /// The subject being suggested
  final PathSubject subject;

  /// Human-readable message explaining the suggestion
  final String message;

  /// Accuracy percentage of the rule
  final double accuracy;

  /// Type of rule condition
  final RuleType ruleType;

  /// Priority level (1 = highest, 4 = lowest)
  final int priority;

  /// Related subject for action-based rules (e.g., take_before)
  final PathSubject? relatedSubject;

  /// Suggested semester for positioning the subject
  final Semester? suggestedSemester;

  /// Whether the suggestion has been accepted
  final bool accepted;

  /// Whether the suggestion has been read
  final bool read;

  /// Whether the suggestion should be displayed
  bool get shouldDisplay => !accepted && !read;

  RuleSuggestion copyWith({
    bool? accepted,
    bool? read,
  }) {
    return RuleSuggestion(
      subject: subject,
      message: message,
      accuracy: accuracy,
      ruleType: ruleType,
      priority: priority,
      relatedSubject: relatedSubject,
      suggestedSemester: suggestedSemester,
      accepted: accepted ?? this.accepted,
      read: read ?? this.read,
    );
  }

  @override
  List<Object?> get props => [
        subject,
        message,
        accuracy,
        ruleType,
        priority,
        relatedSubject,
        suggestedSemester,
        accepted,
        read,
      ];
}
