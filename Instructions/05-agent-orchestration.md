---
lab:
    title: 'Develop a multi-agent solution with Semantic Kernel'
    description: 'Learn to configure multiple agents to collaborate using the Semantic Kernel SDK'
---

# Develop a multi-agent solution

In this exercise, you'll practice using the sequential orchestration pattern in the Semantic Kernel SDK. You'll create a simple pipeline of three agents that work together to process customer feedback and suggest next steps. You'll create the following agents:

- The Summarizer agent will condense raw feedback into a short, neutral sentence.
- The Classifier agent will categorize the feedback as Positive, Negative, or a Feature request.
- Finally, the Recommended Action agent will recommend an appropriate follow-up step.

You'll learn how to use the Semantic Kernel SDK to break down a problem, route it through the right agents, and produce actionable results. Let's get started!

> **Tip**: The code used in this exercise is based on the for Semantic Kernel SDK for Python. You can develop similar solutions using the SDKs for Microsoft .NET and Java. Refer to [Supported Semantic Kernel languages](https://learn.microsoft.com/semantic-kernel/get-started/supported-languages) for details.

This exercise should take approximately **30** minutes to complete.

> **Note**: Some of the technologies used in this exercise are in preview or in active development. You may experience some unexpected behavior, warnings, or errors.

## Deploy a model in an Azure AI Foundry project

Let's start by deploying a model in an Azure AI Foundry project.

1. In a web browser, open the [Azure AI Foundry portal](https://ai.azure.com) at `https://ai.azure.com` and sign in using your Azure credentials. Close any tips or quick start panes that are opened the first time you sign in, and if necessary use the **Azure AI Foundry** logo at the top left to navigate to the home page, which looks similar to the following image (close the **Help** pane if it's open):

    ![Screenshot of Azure AI Foundry portal.](./Media/ai-foundry-home.png)

1. In the home page, in the **Explore models and capabilities** section, search for the `gpt-4o` model; which we'll use in our project.
1. In the search results, select the **gpt-4o** model to see its details, and then at the top of the page for the model, select **Use this model**.
1. When prompted to create a project, enter a valid name for your project and expand **Advanced options**.
1. Confirm the following settings for your project:
    - **Azure AI Foundry resource**: *A valid name for your Azure AI Foundry resource*
    - **Subscription**: *Your Azure subscription*
    - **Resource group**: *Create or select a resource group*
    - **Region**: *Select any **AI Services supported location***\*

    > \* Some Azure AI resources are constrained by regional model quotas. In the event of a quota limit being exceeded later in the exercise, there's a possibility you may need to create another resource in a different region.

1. Select **Create** and wait for your project, including the gpt-4 model deployment you selected, to be created.

1. When your project is created, the chat playground will be opened automatically.

1. In the navigation pane on the left, select **Models and endpoints** and select your **gpt-4o** deployment.

1. In the **Setup** pane, note the name of your model deployment; which should be **gpt-4o**. You can confirm this by viewing the deployment in the **Models and endpoints** page (just open that page in the navigation pane on the left).
1. In the navigation pane on the left, select **Overview** to see the main page for your project; which looks like this:

    ![Screenshot of a Azure AI project details in Azure AI Foundry portal.](./Media/ai-foundry-project.png)

## Create an AI Agent client app

Now you're ready to create a client app that defines an agent and a custom function. Some code is provided for you in a GitHub repository.

### Prepare the environment

1. Open a new browser tab (keeping the Azure AI Foundry portal open in the existing tab). Then in the new tab, browse to the [Azure portal](https://portal.azure.com) at `https://portal.azure.com`; signing in with your Azure credentials if prompted.

    Close any welcome notifications to see the Azure portal home page.

1. Use the **[\>_]** button to the right of the search bar at the top of the page to create a new Cloud Shell in the Azure portal, selecting a ***PowerShell*** environment with no storage in your subscription.

    The cloud shell provides a command-line interface in a pane at the bottom of the Azure portal. You can resize or maximize this pane to make it easier to work in.

    > **Note**: If you have previously created a cloud shell that uses a *Bash* environment, switch it to ***PowerShell***.

1. In the cloud shell toolbar, in the **Settings** menu, select **Go to Classic version** (this is required to use the code editor).

    **<font color="red">Ensure you've switched to the classic version of the cloud shell before continuing.</font>**

1. In the cloud shell pane, enter the following commands to clone the GitHub repo containing the code files for this exercise (type the command, or copy it to the clipboard and then right-click in the command line and paste as plain text):

    ```
   rm -r ai-agents -f
   git clone https://github.com/MicrosoftLearning/mslearn-ai-agents ai-agents
    ```

    > **Tip**: As you enter commands into the cloud shell, the output may take up a large amount of the screen buffer and the cursor on the current line may be obscured. You can clear the screen by entering the `cls` command to make it easier to focus on each task.

1. When the repo has been cloned, enter the following command to change the working directory to the folder containing the code files and list them all.

    ```
   cd ai-agents/Labfiles/05-agent-orchestration/Python
   ls -a -l
    ```

    The provided files include application code and a file for configuration settings.

### Configure the application settings

1. In the cloud shell command-line pane, enter the following command to install the libraries you'll use:

    ```
   python -m venv labenv
   ./labenv/bin/Activate.ps1
   pip install python-dotenv azure-identity semantic-kernel --upgrade
    ```

    > **Note**: Installing *semantic-kernel* automatically installs a semantic kernel-compatible version of *azure-ai-projects*.

1. Enter the following command to edit the configuration file that is provided:

    ```
   code .env
    ```

    The file is opened in a code editor.

1. In the code file, replace the **your_openai_endpoint** placeholder with the Azure Open AI endpoint for your project (copied from the project **Overview** page in the Azure AI Foundry portal under **Azure OpenAI**). Replace the **your_openai_api_key** with the API Key for your project, and ensure that the MODEL_DEPLOYMENT_NAME variable is set to your model deployment name (which should be *gpt-4o*).

1. After you've replaced the placeholders, use the **CTRL+S** command to save your changes and then use the **CTRL+Q** command to close the code editor while keeping the cloud shell command line open.

### Create AI agents

Now you're ready to create the  agents for your multi-agent solution! Let's get started!

1. Enter the following command to edit the **agents.py** file:

    ```
   code agents.py
    ```

1. At the top of the file under the comment **Add references**, and add the following code to reference the namespaces in the libraries you'll need to implement your agent:

    ```python
   # Add references
   import asyncio
   from semantic_kernel.agents import Agent, ChatCompletionAgent, SequentialOrchestration
   from semantic_kernel.agents.runtime import InProcessRuntime
   from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
   from semantic_kernel.contents import ChatMessageContent
    ```


1. In the **get_agents** function, add the following code under the comment **Create a summarizer agent**:

    ```python
   # Create a summarizer agent
   summarizer_agent = ChatCompletionAgent(
       name="SummarizerAgent",
       instructions="""
       Summarize the customer's feedback in one short sentence. Keep it neutral and concise.
       Example output:
       App crashes during photo upload.
       User praises dark mode feature.
       """,
       service=AzureChatCompletion(),
   )
    ```

1. Add the following code under the comment **Create a classifier agent**:

    ```python
   # Create a classifier agent
   classifier_agent = ChatCompletionAgent(
       name="ClassifierAgent",
       instructions="""
       Classify the feedback as one of the following: Positive, Negative, or Feature request.
       """,
       service=AzureChatCompletion(),
   )
    ```

1. Add the following code under the comment **Create a recommended action agent**:

    ```python
   # Create a recommended action agent
   action_agent = ChatCompletionAgent(
       name="ActionAgent",
       instructions="""
       Based on the summary and classification, suggest the next action in one short sentence.
       Example output:
       Escalate as a high-priority bug for the mobile team.
       Log as positive feedback to share with design and marketing.
       Log as enhancement request for product backlog.
       """,
       service=AzureChatCompletion(),
   )
    ```

1. Add the following code under the comment **Return a list of agents**:

    ```python
   # Return a list of agents
   return [summarizer_agent, classifier_agent, action_agent]
    ```

    The order of the agents in this list will be the order that they are selected during the orchestration.

## Create a sequential orchestration

1. In the **main** function, find the comment **Initialize the input task** and add the following code:
    
    ```python
   # Initialize the input task
   task="""
   I tried updating my profile picture several times today, but the app kept freezing halfway through the process. 
   I had to restart it three times, and in the end, the picture still wouldn't upload. 
   It's really frustrating and makes the app feel unreliable.
   """
    ```

1. Under the comment **Create a sequential orchestration**, add the following code to define a sequential orchestration with a response callback:

    ```python
   # Create a sequential orchestration
   sequential_orchestration = SequentialOrchestration(
       members=get_agents(),
       agent_response_callback=agent_response_callback,
   )
    ```

    The `agent_response_callback` will allow you to view the response from each agent during the orchestration.

1. Add the following code under the comment **Create a runtime and start it**:

    ```python
   # Create a runtime and start it
   runtime = InProcessRuntime()
   runtime.start()
    ```

1. Add the following code under the comment **Invoke the orchestration with a task and the runtime**:

    ```python
   # Invoke the orchestration with a task and the runtime
   orchestration_result = await sequential_orchestration.invoke(
       task=task,
       runtime=runtime,
   )
    ```

1. Add the following code under the comment **Wait for the results**:

    ```python
   # Wait for the results
   value = await orchestration_result.get(timeout=20)
   print(f"\n****** Task Input ******{task}")
   print(f"***** Final Result *****\n{value}")
    ```

    In this code, you retrieve and display the result of the orchestration. If the orchestration does not complete within the specified timeout, a timeout exception will be thrown.

1. Find the comment **Stop the runtime when idle**, and add the following code:

    ```python
   # Stop the runtime when idle
   await runtime.stop_when_idle()
    ```

    After processing is complete, stop the runtime to clean up resources.

1. Use the **CTRL+S** command to save your changes to the code file. You can keep it open (in case you need to edit the code to fix any errors) or use the **CTRL+Q** command to close the code editor while keeping the cloud shell command line open.

### Sign into Azure and run the app

Now you're ready to run your code and watch your AI agents collaborate.

1. In the cloud shell command-line pane, enter the following command to sign into Azure.

    ```
   az login
    ```

    **<font color="red">You must sign into Azure - even though the cloud shell session is already authenticated.</font>**

    > **Note**: In most scenarios, just using *az login* will be sufficient. However, if you have subscriptions in multiple tenants, you may need to specify the tenant by using the *--tenant* parameter. See [Sign into Azure interactively using the Azure CLI](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively) for details.

1. When prompted, follow the instructions to open the sign-in page in a new tab and enter the authentication code provided and your Azure credentials. Then complete the sign in process in the command line, selecting the subscription containing your Azure AI Foundry hub if prompted.

1. After you have signed in, enter the following command to run the application:

    ```
   python agents.py
    ```

    You should see some output similar to the following:

    ```output
    # SummarizerAgent
    App freezes during profile picture upload, preventing completion.
    # ClassifierAgent
    Negative
    # ActionAgent
    Escalate as a high-priority bug for the development team.

    ****** Task Input ******
    I tried updating my profile picture several times today, but the app kept freezing halfway through the process.
    I had to restart it three times, and in the end, the picture still wouldn't upload.
    It's really frustrating and makes the app feel unreliable.

    ***** Final Result *****
    Escalate as a high-priority bug for the development team.
    ```

1. Optionally, you can try running the code using different task inputs, such as:

    ```output
    I use the dashboard every day to monitor metrics, and it works well overall. But when I'm working late at night, the bright screen is really harsh on my eyes. If you added a dark mode option, it would make the experience much more comfortable.
    ```
    ```output
    I reached out to your customer support yesterday because I couldn't access my account. The representative responded almost immediately, was polite and professional, and fixed the issue within minutes. Honestly, it was one of the best support experiences I've ever had.
    ```

## Summary

In this exercise, you practiced sequential orchestration with the Semantic Kernel SDK, combining multiple agents into a single, streamlined workflow. Great work!

## Clean up

If you've finished exploring Azure AI Agent Service, you should delete the resources you have created in this exercise to avoid incurring unnecessary Azure costs.

1. Return to the browser tab containing the Azure portal (or re-open the [Azure portal](https://portal.azure.com) at `https://portal.azure.com` in a new browser tab) and view the contents of the resource group where you deployed the resources used in this exercise.

1. On the toolbar, select **Delete resource group**.

1. Enter the resource group name and confirm that you want to delete it.
