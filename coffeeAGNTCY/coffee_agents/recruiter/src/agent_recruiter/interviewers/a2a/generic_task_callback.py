# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Handles generic task updates for A2A agents.

a2a-sdk 1.x clients yield ``StreamResponse`` events (a ``payload`` oneof of
``task``, ``message``, ``status_update`` or ``artifact_update``). This callback
folds the task, status and artifact events into one ``Task`` per task id.
"""

from a2a.types import (
    AgentCard,
    Artifact,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskState,
)


class GenericTaskUpdateCallback:
    def __init__(self) -> None:
        self._task_id_to_task: dict[str, Task] = {}

    def task_callback(self, event: StreamResponse, _: AgentCard) -> Task | None:
        """Fold ``event`` into its task and return the task so far.

        Returns ``None`` for an event that carries no task data (a message).
        """
        which = event.WhichOneof("payload")
        if which == "task":
            task = Task()
            task.CopyFrom(event.task)
            self._task_id_to_task[task.id] = task
            return task
        if which == "status_update":
            return self._task_status_update_callback(event.status_update)
        if which == "artifact_update":
            return self._task_artifact_update_callback(event.artifact_update)
        return None

    def _task_status_update_callback(self, event: TaskStatusUpdateEvent) -> Task:
        task = self._task_id_to_task.get(event.task_id)
        if task is None:
            task = Task(
                context_id=event.context_id,
                id=event.task_id,
                status=event.status,
            )
            if event.HasField("metadata"):
                task.metadata.CopyFrom(event.metadata)
        else:
            if event.HasField("metadata"):
                task.metadata.MergeFrom(event.metadata)

            if not task.status.HasField("message"):
                if event.status.HasField("message"):
                    task.status.message.CopyFrom(event.status.message)
            elif event.status.HasField("message"):
                task.status.message.parts.extend(event.status.message.parts)
            if event.status.HasField("timestamp"):
                task.status.timestamp.CopyFrom(event.status.timestamp)
            task.status.state = event.status.state

        self._task_id_to_task[event.task_id] = task
        return task

    def _task_artifact_update_callback(self, event: TaskArtifactUpdateEvent) -> Task:
        task = self._task_id_to_task.get(event.task_id)
        if task is None:
            task = Task(
                artifacts=[event.artifact],
                context_id=event.context_id,
                id=event.task_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
            if event.HasField("metadata"):
                task.metadata.CopyFrom(event.metadata)
        else:
            if not event.append:  # append means appending to a previous artifact
                task.artifacts.append(event.artifact)
            else:
                current_artifact = self._get_artifact_by_id(
                    list(task.artifacts),
                    event.artifact.artifact_id,
                )
                if current_artifact is None:
                    task.artifacts.append(event.artifact)
                else:
                    self._merge_artifacts(current_artifact, event.artifact)

        self._task_id_to_task[event.task_id] = task
        return task

    @staticmethod
    def _get_artifact_by_id(
        artifacts: list[Artifact] | None,
        artifact_id: str,
    ) -> Artifact | None:
        if artifacts is None:
            return None
        for artifact in artifacts:
            if artifact.artifact_id == artifact_id:
                return artifact
        return None

    @staticmethod
    def _merge_artifacts(
        current_artifact: Artifact,
        new_artifact_data: Artifact,
    ) -> None:
        # parts
        current_artifact.parts.extend(new_artifact_data.parts)

        # metadata
        if new_artifact_data.HasField("metadata"):
            current_artifact.metadata.MergeFrom(new_artifact_data.metadata)

        # description
        if not current_artifact.description:
            current_artifact.description = new_artifact_data.description

        # name
        if not current_artifact.name:
            current_artifact.name = new_artifact_data.name
