# Design

## Context

A documentation-only correction to a living spec. The code, Taskfile task
description, `setup.sh` header and `setup-repo-tooling` skill were already
updated to name every installed tool; the spec is the last place that
still lists the old set.

## Decisions

- Express the change as a single MODIFIED requirement with the full
  replacement text, so archiving rewrites the requirement in place rather
  than adding a parallel one.
- Keep the spec at the level of observable behavior (which tools exist,
  which directories reach `PATH`), not install mechanics such as why bats
  and node get their own directories.
