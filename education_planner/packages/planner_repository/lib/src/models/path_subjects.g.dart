// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'path_subjects.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PathSubject _$PathSubjectFromJson(Map<String, dynamic> json) => PathSubject(
      id: stringToInt(json['id']),
      name: json['name'] as String,
      semester: (json['semester'] as num?)?.toDouble() ?? 0,
      subjectIds: (json['subjectIds'] as List<dynamic>?)
              ?.map((e) => (e as num).toInt())
              .toList() ??
          const [],
      status: json['status'] as String? ?? '',
    );

Map<String, dynamic> _$PathSubjectToJson(PathSubject instance) =>
    <String, dynamic>{
      'id': intToString(instance.id),
      'name': instance.name,
      'semester': instance.semester,
      'status': instance.status,
      'subjectIds': instance.subjectIds,
    };
