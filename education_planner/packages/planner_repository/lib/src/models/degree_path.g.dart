// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'degree_path.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DegreePath _$DegreePathFromJson(Map<String, dynamic> json) => DegreePath(
      id: (json['id'] as num).toInt(),
      degree: json['degree'] as String,
      subjects: (json['subjects'] as List<dynamic>)
          .map((e) => PathSubject.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$DegreePathToJson(DegreePath instance) =>
    <String, dynamic>{
      'id': instance.id,
      'degree': instance.degree,
      'subjects': instance.subjects.map((e) => e.toJson()).toList(),
    };
