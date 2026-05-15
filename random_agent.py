import rlcard
from rlcard.agents import RandomAgent
from cribbage.env.cribbage import CribbageEnv

def test_cribbage_env():
    # 1. Initialize the environment directly
    env = CribbageEnv(config={'seed': 42})
    
    # 2. Set up Random Agents for both players
    # RandomAgent simply picks a random action from `legal_actions`
    agents = [RandomAgent(num_actions=env.num_actions) for _ in range(env.num_players)]
    env.set_agents(agents)

    # 3. Generate a complete game trajectory
    # This runs the game from start to finish
    trajectories, payoffs = env.run(is_training=False)

    # 4. Print the results
    print("Game Finished!")
    print(f"Final Payoffs: {payoffs}")
    
    # Print the last few states to see how the game ended
    print("\nLast State (Player 0):")
    final_state = trajectories[0][-1]['raw_obs']
    print(f"Hand: {final_state['hand']}")
    print(f"Scores: {final_state['scores']}")

if __name__ == "__main__":
    test_cribbage_env()