CREATE TABLE policy (
    policy_id int NOT NULL,
    expand_ratio float,
    shrink_ratio float,
    cpu_util_grow_threshold float,
    cpu_util_shrink_threshold float,
    PRIMARY KEY (policy_id)
)ENGINE=InnoDB;

INSERT INTO policy (policy_id, expand_ratio, shrink_ratio, cpu_util_grow_threshold, cpu_util_shrink_threshold) VALUES (1, 2.0, 0.5, 60, 10);