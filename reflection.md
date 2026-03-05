# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the secret number kept changing" or "the hints were backwards").
When I first launched it I had problems (that shouldn't have been there to begin with), this came from an error setting up my venv, and a conflict with dependicies/packages. I figured that out then I was able to run everything properly. The first error I noticed were the Hints switching between saying higher/lower, when i continued to input the same number. Another issue regarding the hint function was with it misshadling an edge case (guess between 0-100, i input 100, it said higher). I also noticed a delay in the history, as well as needing to refresh the page to start a new game. 
---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).

I am using claude cod to help with this project. One example of it being correct (basically every example so far), is it finding the exact lines/blocks of code causing the errors, based off my description of the problem. I verified it by looking at each code section where it described the error and following it's logic to see if it was accurate.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- In your own words, explain why the secret number kept changing in the original app.
- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
- What change did you make that finally gave the game a stable secret number?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
