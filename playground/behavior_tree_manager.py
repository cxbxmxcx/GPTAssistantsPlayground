import os
import threading
import time
from prefect import flow
import yaml
import py_trees
from py_trees.trees import BehaviourTree

from playground.behavior_trees import create_assistant_action


@flow(log_prints=True)
def deployment_run_btree(yaml_path, tick_interval=30):
    btm = BehaviorTreeManager(os.path.dirname(yaml_path))
    tree = btm.load_behavior_tree_from_yaml(yaml_path)
    while True:
        tree.tick()
        if tree.root.status == py_trees.common.Status.SUCCESS:
            print("Behavior tree completed successfully.")
            break
        if tree.root.status == py_trees.common.Status.FAILURE:
            print("Behavior tree failed.")
            break
        time.sleep(tick_interval)


class BehaviorTreeManager:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_tree_runner = None

    def load_yaml_files(self):
        yaml_files = [
            f
            for f in os.listdir(self.folder_path)
            if f.endswith(".yaml") or f.endswith(".yml")
        ]
        summaries = []
        for file in yaml_files:
            with open(os.path.join(self.folder_path, file), "r") as f:
                data = yaml.safe_load(f)
                summaries.append(data["behavior_tree"]["name"])
        return yaml_files, summaries

    def load_behavior_tree_from_yaml(self, yaml_path):
        with open(yaml_path, "r") as file:
            data = yaml.safe_load(file)

        def create_node(node_data):
            node_type = node_data["type"]
            if node_type in ["Sequence", "Selector"]:
                node_class = (
                    py_trees.composites.Sequence
                    if node_type == "Sequence"
                    else py_trees.composites.Selector
                )
                node = node_class(
                    node_data.get("name", ""), memory=node_data.get("memory", False)
                )
                for child_data in node_data.get("children", []):
                    child_node = create_node(child_data)
                    node.add_child(child_node)
            elif node_type == "Action":
                node = create_assistant_action(
                    action_name=node_data["name"],
                    assistant_name=node_data["agent"],
                    assistant_instructions=node_data["instructions"],
                )
            elif node_type == "Condition":
                node = py_trees.behaviours.CheckBlackboardVariableExists(
                    name=node_data["name"], variable_name=node_data["name"]
                )
            else:
                raise ValueError(f"Unknown node type: {node_type}")
            return node

        root_data = data["behavior_tree"]["root"]
        root = create_node(root_data)
        return BehaviourTree(root)

    # def deploy_behavior_tree(
    #     self, yaml_path, deployment_name="Behavior Tree Deployment"
    # ):
    #     deployment_run_btree.serve(deployment_name, parameters={"yaml_path": yaml_path})

    #     return f"Behavior tree: {deployment_name}, is deployed."

    def deploy_behavior_tree(self, yaml_path):
        deployment_name = os.path.splitext(os.path.basename(yaml_path))[0]

        def deploy_flow():
            deployment_run_btree.serve(
                deployment_name, parameters={"yaml_path": yaml_path}
            )

        deploy_thread = threading.Thread(target=deploy_flow)
        deploy_thread.start()

        return f"Behavior tree: {deployment_name}, is deployed."


@flow(log_prints=True)
def run_btree(btree_runner):
    while not btree_runner._stop_event.is_set():
        btree_runner.tree.tick()
        if btree_runner.tree.root.status == py_trees.common.Status.SUCCESS:
            print("Behavior tree completed successfully.")
            break
        if btree_runner.tree.root.status == py_trees.common.Status.FAILURE:
            print("Behavior tree failed.")
            break
        time.sleep(btree_runner.tick_interval)


class BehaviorTreeRunner(threading.Thread):
    def __init__(self, tree, tick_interval=30):
        super().__init__()
        self.tree = tree
        self.tick_interval = tick_interval
        self._stop_event = threading.Event()

    def run(self):
        run_btree(self)

    def stop(self):
        self._stop_event.set()
