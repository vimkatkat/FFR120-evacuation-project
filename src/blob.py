# blob.py
import numpy as np


class Blob:
    def __init__(self, angle, x, y, threshold, min_velocity):
        self.angle = angle
        self.x = x
        self.y = y
        self.velocity = np.array([0.0, 0.0])
        self.threshold = threshold
        self.min_velocity = min_velocity

    def get_quadrant(self, D):
        if self.x >= D/2 and self.y >= D/2:
            return 1
        elif self.x < D/2 and self.y > D/2:
            return 2
        elif self.x < D/2 and self.y < D/2:
            return 3
        else:
            return 4

    def get_second_closest_exit(self, exit_points):
        distances = []
        for point in exit_points:
            distances.append(np.sqrt((self.x - point[0]) ** 2 + (self.y - point[1]) ** 2))

        if len(distances) >= 2:
            sorted_indices = np.argsort(distances)
            second_closest_index = sorted_indices[1]
            second_closest_exit = exit_points[second_closest_index]
            return second_closest_exit
        else:
            return None

    def check_proximity(self, blobs, threshold, min_velocity):
        close_blobs = 0
        for other_blob in blobs:
            if other_blob is not self:
                distance = np.sqrt((self.x - other_blob.x)**2 + (self.y - other_blob.y)**2)
                if distance < threshold:
                    close_blobs += 1
        if close_blobs >= 2:
            self.velocity /= 1.1
            self.velocity = np.maximum(self.velocity, min_velocity)

    def closest_checkpoint(self, checkpoints):
        distances = [np.linalg.norm(np.array([self.x, self.y]) - cp) for cp in checkpoints]
        closest_index = np.argmin(distances)
        return checkpoints[closest_index]

    # exit_point[0] = np.array([D/2, D])  # TOP
    # exit_point[1] = np.array([D, D/2])  # RIGHT
    # exit_point[2] = np.array([0, D/2])  # LEFT
    # exit_point[3] = np.array([D/2, 0])  # BOT
    def update(
       self,
       exit_points,
       checkpoints,
       alarm_on,
       stepsize,
       eta,
       D,
       blobs,
       threshold,
       min_velocity,
       max_velocity,
       turn_around_steps,
       exit_counter,
       exited_blobs,
    ):
        # Check if the blob has reached the exit point
        if np.linalg.norm(np.array([self.x, self.y]) - exit_points[1]) < 0.25:
            exit_counter += 1
            exited_blobs.add(self)
            return
        self.check_proximity(blobs, threshold, min_velocity)
        if alarm_on:
            quadrant = self.get_quadrant(D)
            if quadrant == 3:
                if not hasattr(self, "reached_checkpoint_0"):
                    closest_cp = self.closest_checkpoint(checkpoints)
                    if (
                        np.linalg.norm(np.array([self.x, self.y]) - checkpoints[0])
                        < 3
                    ):
                        self.reached_checkpoint_0 = True
                    preferred_exit = (
                        exit_points[0]
                        if hasattr(self, "reached_checkpoint_0")
                        else closest_cp
                    )
                elif not hasattr(self, "reached_checkpoint_1"):
                    closest_cp = self.closest_checkpoint(checkpoints)
                    if (
                        np.linalg.norm(np.array([self.x, self.y]) - checkpoints[1])
                        < 3
                    ):
                        self.reached_checkpoint_1 = True
                    preferred_exit = (
                        exit_points[1]
                        if hasattr(self, "reached_checkpoint_1")
                        else closest_cp
                    )
                else:
                    preferred_exit = exit_points[0]
            elif quadrant == 1:
                preferred_exit = exit_points[0]
            elif quadrant == 2:
                preferred_exit = exit_points[0]
            elif quadrant == 4:
                preferred_exit = exit_points[1]
            else:
                preferred_exit = exit_points[0]

            exit_direction = np.arctan2(
                preferred_exit[1] - self.y, preferred_exit[0] - self.x
            )

            if np.linalg.norm(self.velocity) > max_velocity:
                second_closest_exit = self.get_second_closest_exit(exit_points)
                if hasattr(self, "turn_around_count") and self.turn_around_count > 0:
                    exit_direction = np.arctan2(
                        second_closest_exit[1] - self.y, second_closest_exit[0] - self.x
                    )
                    self.angle = 0.5 * self.angle + 0.5 * exit_direction
                    self.angle = self.angle
                    v = (
                        self.velocity
                        * 0.5
                        * np.array([np.cos(self.angle), np.sin(self.angle)])
                    )
                    self.turn_around_count -= 1
                else:
                    # self.turn_around_count = turn_around_steps
                    exit_direction = np.arctan2(
                        preferred_exit[1] - self.y, preferred_exit[0] - self.x
                    )

            self.angle = 0.5 * self.angle + 0.5 * exit_direction
            v = self.velocity * np.array([np.cos(self.angle), np.sin(self.angle)])

            proposed_position = np.array([self.x, self.y]) + stepsize * v

            self.x, self.y = np.clip(proposed_position, 0, D)

            # Check if the blob has reached the exit point
            # if np.linalg.norm(np.array([self.x, self.y]) - exit_points[1]) < threshold:
            #     preferred_exit = exit_points[1]
            #     self.velocity = np.array([0.0, 0.0])  # Stop the blob

    def intersects_wall(self, proposed_position, D):
        cross_width = 1  # adjust as needed
        passage_width = 4  # adjust as needed
        x, y = proposed_position

        in_horizontal_cross = (D/2 - cross_width/2 < x < D/2 + cross_width/2) and not (passage_width < y < D - passage_width)
        in_vertical_cross = (D/2 - cross_width/2 < y < D/2 + cross_width/2) and not (passage_width < x < D - passage_width)

        return in_horizontal_cross or in_vertical_cross

