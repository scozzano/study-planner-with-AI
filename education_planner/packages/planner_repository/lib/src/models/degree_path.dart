import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:planner_repository/planner_repository.dart';

part 'degree_path.g.dart';

@JsonSerializable(explicitToJson: true)

/// Represents a degree path in the education system.
class DegreePath extends Equatable {
  /// Creates a new instance of [DegreePath].
  const DegreePath({
    required this.id,
    required this.degree,
    required this.subjects,
  });

  /// Creates a new instance of [DegreePath] from a JSON object.
  factory DegreePath.fromJson(Map<String, dynamic> json) =>
      _$DegreePathFromJson(json);

  /// Converts the [DegreePath] instance to a JSON object.
  Map<String, dynamic> toJson() => _$DegreePathToJson(this);

  /// The unique identifier for the degree path.
  final int id;

  /// The name of the degree associated with the path.
  final String degree;

  /// The list of subjects associated with the degree path.
  final List<PathSubject> subjects;

  @override
  List<Object?> get props => [
        id,
        degree,
        subjects,
      ];
}
