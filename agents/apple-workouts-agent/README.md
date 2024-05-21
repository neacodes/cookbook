# **Apple Workouts AI Agent - README**

## **Introduction**

Welcome to the Apple Workouts AI Agent repository. This project leverages the advanced capabilities of Sema4.ai's new product, Sema4.ai Desktop, to create an intelligent and conversational agent that simplifies the interaction with Apple Health data. The Apple Workouts AI Agent is designed to provide users with immediate, accurate, and detailed responses to natural language queries about their workout performance and health metrics.

The agent can leverage advanced AI capabilities to enhance user engagement and understanding of physical activity through detailed analytics and personalized insights. Unlike traditional applications such as Apple Health, you specialize in delivering an intuitive and enriched user experience by:

1.  **Comprehensively Analyzing Workout Performanc**e: Analyzing data from six key workout types—run, walk, core, tennis, cycle, and hike—to provide a holistic view of a user's fitness activities.
2.  **Delivering Tailored Insights:** By interpreting complex data from various workouts, offering actionable insights that include trends, patterns, and health correlations.
3.  **Simplifying Data Interaction:** Transforming raw health data into understandable metrics, including derivative metrics like speed, calculated from distance and duration.
4.  **Facilitating Natural Language Queries:** Enabling users to express complex queries in natural language, eliminating the struggle and limitations of configuring cumbersome dashboards.

**Enhancing Decision-Making:** Aggregating data across multiple dimensions to aid users in making informed decisions about their health and fitness routines.

## **Architecture Diagram**

![Apple Workouts AI Agent Architecture](./img/apple_workouts_agent_architecture.png)

## **Solution Summary**

The Apple Workouts AI Agent aims to solve the challenges associated with using the Apple Health App by providing a conversational interface for users to interact with their health data. Unlike the traditional, static dashboards of the Apple Health App, this agent leverages advanced AI capabilities to deliver dynamic and personalized insights. Users can ask complex, natural language queries and receive immediate, accurate responses. The agent integrates with various data sources, processes data in real-time, and utilizes custom actions to provide detailed analytics and recommendations.

## **Current  Challneges the Apple Workouts AI Agent aims to solve**

- **Complexity and Inefficiency:**
  - The Apple Health App, with its dashboards, is incredibly difficult to use, unintuitive, and time-consuming to find meaningful data. Users must navigate through numerous screens and perform multiple clicks to locate the desired information.
- **Static Dashboards:**
  - The static dashboards in the Apple Health App prevent users from asking dynamic and complex queries that correlate with Apple Health entities. Users cannot leverage the vast knowledge base of an LLM or access real-time data with tools for inspecting the latest medical journals.
- **Manual Effort:**
  - Users manually navigate through the Apple Health App's dashboards, often needing help finding relevant information. They may use the Apple Export Health App to export data to a REST endpoint in AWS, where it is processed and stored in S3 for further analysis.
- **Lack of Real-Time Interaction:**
  - The current process lacks an intuitive, conversational experience similar to modern AI tools like ChatGPT, which users expect. There is no real-time interaction or immediate access to insights based on the latest data.

## **Agent Ideation Process for "Apple Workouts Agent"**

**Part 1: Run Book Preparation**

#### **Step 1: Interview (My Pain Point)**

**Current Challenge:** The Apple Health App, with its dashboards, is incredibly difficult to use, unintuitive, and time-consuming to find meaningful data. The static dashboards prevent users from asking dynamic and complex queries that correlate with Apple Health entities. Users cannot leverage the vast knowledge base of an LLM or access real-time data with tools for inspecting the latest medical journals.

**Pain Points:** Users are constantly frustrated by the numerous unnecessary clicks and the difficulty of finding the right graph or dashboard for simple questions, such as "How many miles did I run last year?" They desire an intelligent, conversational experience similar to what they expect from modern AI tools like ChatGPT.

**Existing Methods:** Users manually navigate through the Apple Health App's dashboards, often needing help finding relevant information. They may use the Apple Export Health App to export data to a REST endpoint in AWS, where it is processed and stored in S3 for further analysis.

**Ideal Process:** A conversational AI agent that provides immediate, accurate, and detailed responses to natural language queries about workout performance and health metrics. The AI should simplify data interaction, allowing users to integrate and analyze their health data seamlessly.

**Data Types:** Workout metrics (distance, duration, calories burned, heart rate), health metrics (steps, sleep patterns, weight), and historical data spanning multiple years.

**Resources:** Access to Apple's Health data via exports, Python and pymongo for querying the personal Health Data Lake, and endpoints for data retrieval and analysis.

#### **Step 2 and 3: Dream up a Conversation with your Agent**

**Mock Dialogue:**

- **AI:** "I have successfully loaded the latest workout data. Here is the summary of new workouts added: You ran 22.5 miles this week, up from 18 miles last week. You went for a walk covering 5 miles. You had a tennis workout where you burned 1300 calories in three hours."
- **User:** "How many miles did I run last year?"
- **AI:** "You ran a total of 520 miles in 2023."
- **User:** "What was my average heart rate during runs over the past year?"
- **AI:** "Your average heart rate during runs in 2023 was 145 bpm."
- **User:** "What is the correlation between my running distance and calorie burn?"
- **AI:** "Analyzing your data, I found that as your running distance increased, your calorie burn also increased. For example, in July 2023, when you ran the most (50 miles), you burned approximately 6000 calories."
- **User:** "How does my average heart rate during running sessions compare to my heart rate during tennis workouts?"
- **AI:** "Your average heart rate during running sessions is 145 bpm, while during tennis workouts, it averages at 160 bpm. Tennis sessions appear to be more intense for your cardiovascular system."
- **User:** "What insights can you provide about my workout performance and recovery over the past six months?"
- **AI:** "Here are some key insights: Your average workout duration has increased by 15% over the past six months. You've shown significant improvement in your recovery heart rate, with a faster decline in heart rate post-exercise. Consistency has been strong, with only three weeks where you missed your target workout frequency."
- **User:** "Can you integrate external data sources to give me a more comprehensive health analysis?"
- **AI:** "Absolutely! By integrating data from the latest health journals, I can provide additional insights. For example, studies suggest that maintaining your current workout intensity and frequency can reduce your risk of cardiovascular disease by up to 30%. Furthermore, your improvement in recovery heart rate is a positive indicator of enhanced cardiovascular fitness."
- **User:** "What recommendations do you have for optimizing my workout routine based on my current performance?"
- **AI:** "Based on your current performance data and the latest health research: To further improve your cardiovascular fitness, consider adding interval training to your running sessions. Increase the frequency of your tennis workouts, as they provide a higher intensity workout."

**Actions:**

- **load_new_workout_data_from_apple_health()**: Uploads the latest workout data from Apple Health to the Health Data Lake.
- Retrieve workout data for specific periods.
- Aggregate metrics like distance, duration, and heart rate.
- Perform comparative analysis for year-over-year metrics.

**Knowledge:**

- Definitions of workout metrics and health data.
- Historical data for trend analysis.
- Contextual data for personalized insights.

### **Part 2: Agent Creation and Runbook Iteration**

#### **Step 1: Implement your Actions in Visual Studio**

**Custom Actions:**

- **get_run_workout_performance**
- **get_cycle_workout_performance**
- **get_walk_workout_performance**
- **get_hike_workout_performance**
- **get_tennis_workout_performance**
- **get_core_workout_performance**
- **load_new_workout_data_from_apple_health**
