from ResAlloc_env import *
from trainer import *
from NN import *
from replay import ReplayMemory
from mcts import *

import random

if __name__ == '__main__':

    def reverse_input(boof):
        wow = []
        for row in boof:
            wow.append(np.sum(row))
        return wow

    env = gameEnv(0)
    representation = Representation(lambda: RepresentationFunc(4,8,2))

    trainer_board = Trainer(lambda: GCNBoard(env.n_resources+2, 8, env.n_resources, env.n_nodes, 0.2), representation, env, 'board')
    trainer_node = []
    for i in range(env.adj.shape[0]):
        trainer_node.append(Trainer(lambda: GCNNode(env.n_resources+2, 8, env.degree[i], env.n_nodes, 0.2, 'node'+str(i)), representation, env, 'node'))
    trainer_score = ScorePredictionTrainer(lambda: ScorePredictionFunc(env.n_resources+2, 8, env.n_nodes, 0.2), representation, env)

    mem_scores = ReplayMemory(500, {"sts" : [env.adj.shape[0], env.n_resources], "features" : [env.features.shape[0], env.features.shape[1]], "scores" : []}, batch_size = 20)
    mem_board = ReplayMemory(100, {"sts" : [env.adj.shape[0], env.n_resources], "features" : [env.features.shape[0], env.features.shape[1]], "pi" : [env.n_resources+1], "return" : []})
    mem_node = []
    for i in range(env.adj.shape[0]):
        mem_node.append(ReplayMemory(100, {"sts" : [env.adj.shape[0], env.n_resources], "features" : [env.features.shape[0], env.features.shape[1]], "pi" : [env.degree[i]], "return" : []}))

    lr = 1.0

    cunt = [0.0]*10
    print(cunt)
    for i in range(100):
        if (i+1)%10==0:
            lr = lr + 1.0
        scenario = random.randint(0, 9)
        cunt[scenario] += 1.0
        print("\n\nayayayaya -----", i, scenario)
        env = gameEnv(scenario)

        sts_board, searches_pi_board, ret_board, sts_node, searches_pi_node, ret_node, score_sts, scores = execute_episode(trainer_board, trainer_node, trainer_score, representation, 800, env, 'train', 1.0)

        wow = reverse_input(sts_board[-1])
        print(len(sts_board), wow, np.sum(wow*env.out), np.sum(env.out))

        mem_board.add_all({"sts" : sts_board,"features": [env.features]*len(sts_board),  "pi" : searches_pi_board, "return" : ret_board})
        for i in range(env.adj.shape[0]):
            mem_node[i].add_all({"sts" : sts_node[i],"features": [env.features]*len(sts_node[i]), "pi" : searches_pi_node[i], "return" : ret_node[i]})
        mem_scores.add_all({"sts" : score_sts, "features": [env.features]*len(score_sts), "scores": scores})

        if mem_board.count >= 4:
            trainer_board.learning_rate = 0.1/float(lr)
            # print("bt",mem_board.count)
            batch_board = mem_board.get_minibatch()
            #print(batch_board["sts"], batch_board["pi"], batch_board["return"])
            loss = trainer_board.train(batch_board["sts"], batch_board["features"], batch_board["pi"], batch_board["return"])
            #print("pipilika", loss.item())

        for i in range(env.adj.shape[0]):
            # print("nd",i, mem_node[i].count)
            if mem_node[i].count >= 2:
                trainer_node[i].learning_rate = 0.2/float(lr)
                batch_node = mem_node[i].get_minibatch()
                loss = trainer_node[i].train(batch_node["sts"], batch_node["features"], batch_node["pi"], batch_node["return"])

        if mem_scores.count>= 10:
            # print("sc ", mem_scores.count)
            batch_score = mem_scores.get_minibatch()
            loss = trainer_score.train(batch_score["sts"], batch_score["features"], batch_score["scores"])

    print(cunt, "\n-\n-\n")
    for i in range(10):
        print("\nfinalee ", i)
        env = gameEnv(i)

        sts_board, searches_pi_board, ret_board, sts_node, searches_pi_node, ret_node, score_sts, scores = execute_episode(trainer_board, trainer_node, trainer_score, representation, 800, env, 'test', 1.0)

        for i in range(len(sts_board)):
            wow = reverse_input(sts_board[i])
            print(i, wow, np.sum(wow*env.out))
