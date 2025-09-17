import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'dt_recommendation_models.g.dart';

/// Response model for Decision Tree Recommendations
@JsonSerializable(explicitToJson: true)
class DecisionTreeResponse extends Equatable {
  /// Creates a new instance of [DecisionTreeResponse]
  const DecisionTreeResponse({
    required this.scoreDict,
    required this.dtNames,
    required this.figures,
    required this.parsed,
    required this.errorMsg,
  });

  /// Creates a new instance of [DecisionTreeResponse] from a JSON object
  factory DecisionTreeResponse.fromJson(Map<String, dynamic> json) =>
      _$DecisionTreeResponseFromJson(json);

  /// Converts the [DecisionTreeResponse] instance to a JSON object
  Map<String, dynamic> toJson() => _$DecisionTreeResponseToJson(this);

  /// The score dictionary containing metrics for each decision tree
  @JsonKey(name: 'score_dict')
  final Map<String, DecisionTreeScore>? scoreDict;

  /// The names of the decision trees
  @JsonKey(name: 'DT_names')
  final List<String>? dtNames;

  /// Base64 encoded figures/images
  final List<String>? figures;

  /// Parsed decision tree rules as dynamic list
  ///  (can contain strings or objects)
  final List<dynamic>? parsed;

  /// Error message if any
  @JsonKey(name: 'error_msg')
  final String? errorMsg;

  @override
  List<Object?> get props => [scoreDict, dtNames, figures, parsed, errorMsg];
}

/// Model for decision tree score metrics
@JsonSerializable(explicitToJson: true)
class DecisionTreeScore extends Equatable {
  /// Creates a new instance of [DecisionTreeScore]
  const DecisionTreeScore({
    required this.classMetrics,
    required this.accuracy,
  });

  /// Creates a new instance of [DecisionTreeScore] from a JSON object
  factory DecisionTreeScore.fromJson(Map<String, dynamic> json) =>
      _$DecisionTreeScoreFromJson(json);

  /// Converts the [DecisionTreeScore] instance to a JSON object
  Map<String, dynamic> toJson() => _$DecisionTreeScoreToJson(this);

  /// Class-specific metrics
  final Map<String, ClassMetrics>? classMetrics;

  /// Overall accuracy scores
  final List<double>? accuracy;

  @override
  List<Object?> get props => [classMetrics, accuracy];
}

/// Model for class-specific metrics
@JsonSerializable(explicitToJson: true)
class ClassMetrics extends Equatable {
  /// Creates a new instance of [ClassMetrics]
  const ClassMetrics({
    required this.precision,
    required this.recall,
  });

  /// Creates a new instance of [ClassMetrics] from a JSON object
  factory ClassMetrics.fromJson(Map<String, dynamic> json) =>
      _$ClassMetricsFromJson(json);

  /// Converts the [ClassMetrics] instance to a JSON object
  Map<String, dynamic> toJson() => _$ClassMetricsToJson(this);

  /// Precision scores for each class
  final List<double>? precision;

  /// Recall scores for each class
  final List<double>? recall;

  @override
  List<Object?> get props => [precision, recall];
}

/// Model for a decision tree rule
@JsonSerializable(explicitToJson: true)
class DecisionTreeRule extends Equatable {
  /// Creates a new instance of [DecisionTreeRule]
  const DecisionTreeRule({
    required this.condition,
    required this.samples,
    required this.value,
    required this.impurity,
    required this.classDistribution,
  });

  /// Creates a new instance of [DecisionTreeRule] from a JSON object
  factory DecisionTreeRule.fromJson(Map<String, dynamic> json) =>
      _$DecisionTreeRuleFromJson(json);

  /// Converts the [DecisionTreeRule] instance to a JSON object
  Map<String, dynamic> toJson() => _$DecisionTreeRuleToJson(this);

  /// The condition string (e.g., "7663_1 <= 0.5,
  /// 7678_1 <= 0.5, class: 3842_1 > 2.5")
  final String condition;

  /// Number of samples
  final int samples;

  /// Value score
  final double value;

  /// Impurity score
  final double impurity;

  /// Class distribution [count, class_id]
  final List<dynamic>? classDistribution;

  @override
  List<Object?> get props => [
        condition,
        samples,
        value,
        impurity,
        classDistribution,
      ];
}
