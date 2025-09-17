import 'package:education_planner/app/bloc/app_bloc.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:education_planner/schooling/schooling.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class CondensedDrawer extends StatefulWidget {
  const CondensedDrawer({super.key});

  @override
  State<CondensedDrawer> createState() => _CondensedDrawerState();
}

class _CondensedDrawerState extends State<CondensedDrawer>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _expandAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleExpansion() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _animationController.forward();
      } else {
        _animationController.reverse();
      }
    });
  }

  String _getCurrentRoute(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    return location;
  }

  @override
  Widget build(BuildContext context) {
    final currentRoute = _getCurrentRoute(context);

    return AnimatedBuilder(
      animation: _expandAnimation,
      builder: (context, child) {
        return Container(
          width: _isExpanded ? MediaQuery.of(context).size.width * 0.20 : 80,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.secondary,
            borderRadius: const BorderRadius.only(
              topRight: Radius.circular(16),
              bottomRight: Radius.circular(16),
            ),
          ),
          child: Column(
            children: [
              if (_isExpanded)
                Align(
                  alignment: Alignment.topRight,
                  child: IconButton(
                    onPressed: _toggleExpansion,
                    icon: Icon(
                      Icons.close,
                      color: Theme.of(context).colorScheme.onSecondary,
                      size: 14,
                    ),
                  ),
                ),
              Expanded(
                child: Column(
                  children: [
                    _DrawerItem(
                      icon: Icons.school,
                      title: 'Mi Escolaridad',
                      route: SchoolingPage.path,
                      currentRoute: currentRoute,
                      isExpanded: _isExpanded,
                      animation: _expandAnimation,
                      onTap: () {
                        if (!_isExpanded) {
                          _toggleExpansion();
                        }
                        context.go(SchoolingPage.path);
                      },
                    ),
                    _DrawerItem(
                      icon: Icons.calendar_today,
                      title: 'Planificador',
                      route: PlannerPage.path,
                      currentRoute: currentRoute,
                      isExpanded: _isExpanded,
                      animation: _expandAnimation,
                      onTap: () {
                        if (!_isExpanded) {
                          _toggleExpansion();
                        }
                        context.go(PlannerPage.path);
                      },
                    ),
                    const SizedBox(
                      height: 16,
                    ),
                  ],
                ),
              ),
              _DrawerItem(
                icon: Icons.exit_to_app,
                title: 'Salir',
                route: '', // Exit doesn't have a route
                currentRoute: currentRoute,
                isExpanded: _isExpanded,
                animation: _expandAnimation,
                onTap: () {
                  context.read<AppBloc>().add(AppStudentIdRemoved());
                  _toggleExpansion();
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _DrawerItem extends StatelessWidget {
  const _DrawerItem({
    required this.icon,
    required this.title,
    required this.route,
    required this.currentRoute,
    required this.isExpanded,
    required this.animation,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String route;
  final String currentRoute;
  final bool isExpanded;
  final Animation<double> animation;
  final VoidCallback onTap;

  bool get isActive => route.isNotEmpty && currentRoute == route;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        decoration: BoxDecoration(
          color: isActive
              ? Theme.of(context).colorScheme.onTertiary.withValues(alpha: 0.2)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: Theme.of(context).colorScheme.onSecondary,
              size: 24,
            ),
            if (isExpanded) ...[
              const SizedBox(width: 16),
              Expanded(
                child: FadeTransition(
                  opacity: animation,
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Theme.of(context).colorScheme.onSecondary,
                          fontWeight:
                              isActive ? FontWeight.w600 : FontWeight.normal,
                        ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
