axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFToken"
axios.defaults.withCredentials = true;

const { createApp, ref } = Vue

  const app = createApp({
    setup() {
      const message = ref('Hello vue!')
      return {
        message
      }
    },
    delimiters: ["[[", "]]"],
    compilerOptions: {
        delimiters: ["[[", "]]"]
    },
    data() {
        return {
            message: 'Hello Vue!',
            tokens: tokens,

            // Overall
            guessHistory: [],
            noPassages: 0,
            totalGuesses: 0,
            totalCorrect: 0,
            totalSkips: 0,
            totalGuessesPerCorrect: Vue.computed(() => {
                let denominator = this.totalCorrect > 0 ? this.totalCorrect : 1
                let gpt = this.totalGuesses / denominator
                return Math.round(gpt * 100) / 100
            }),
            totalGPT2Guesses: 0,
            totalGPT2SkipGuesses: 0,
            totalGPT2GuessesPerCorrect: Vue.computed(() => {
                let denominator = this.totalCorrect > 0 ? this.totalCorrect : 1
                let gpt = this.totalGPT2Guesses / denominator
                return Math.round(gpt * 100) / 100
            }),
            totalGPT2GuessesPerSkip: Vue.computed(() => {
                let denominator = this.totalSkips > 0 ? this.totalSkips : 1
                let gpt = this.totalGPT2SkipGuesses / denominator
                return Math.round(gpt * 100) / 100
            }),

            // Current Passage
            passage: {},
            passage_tokens: {},
            seen: "",
            unseen: [],
            passageCorrect: 0,
            passageSkips: 0,
            passageGuesses: 0,
            guessesPerCorrect: Vue.computed(() => {
                let denominator = this.passageCorrect > 0 ? this.passageCorrect : 1
                let gpt = this.passageGuesses / denominator
                return Math.round(gpt * 100) / 100
            }),
            passageGPT2Guesses: 0,
            passageGPT2SkipGuesses: 0,
            passageGPT2GuessesPerCorrect: Vue.computed(() => {
                let denominator = this.passageCorrect > 0 ? this.passageCorrect : 1
                let gpt = this.passageGPT2Guesses / denominator
                return Math.round(gpt * 100) / 100
            }),
            passageGPT2GuessesPerSkip: Vue.computed(() => {
                let denominator = this.passageSkips > 0 ? this.passageSkips : 1
                let gpt = this.passageGPT2SkipGuesses / denominator
                return Math.round(gpt * 100) / 100
            }),

            // Last Token
            lastToken: "",
            lastGuesses: null,
            lastGPT2Guesses: null,

            // Current Token
            guesses: [],
            query: "",
            
            tokenOptions: Vue.computed(() => {
                let validTokens = this.tokens.filter((token) => token.includes(this.query) && !this.guesses.includes(token))
                let underscoreTokens = validTokens.map((token) => token.replace(" ", "_"))

                // Filter out duplicates
                let uniqueTokens = [...new Set(underscoreTokens)];

                // Refined sorter: Length first, then underscores (unless it's just punctuation).
                let sortedTokens = uniqueTokens.sort((a, b) => {
                    // Calculate 'real' length without counting underscores
                    let lengthA = a.replace(/_/g, '').length;
                    let lengthB = b.replace(/_/g, '').length;

                    // Sort by length first (shorter wins)
                    if (lengthA !== lengthB) return lengthA - lengthB;

                    // If lengths are equal, and it's not just punctuation, underscore gets priority
                    if (lengthA > 1 || (!a.match(/^\W+$/) && !b.match(/^\W+$/))) {
                        if (a.includes("_") && !b.includes("_")) return -1;
                        if (!a.includes("_") && b.includes("_")) return 1;
                    }

                    return 0; // For equal lengths or just punctuation
                });

                this.selectedToken = sortedTokens[0];
                return sortedTokens.slice(0, 5);
            }),
            selectedToken: "",
            modal: ""
        }
    },
    mounted() {
        this.getSentence();

    },
    methods: {
        guessKeydown(event) {
            // console.log(event.key)
            if (event.key === "ArrowDown") {
                console.log("down")
                let index = this.tokenOptions.indexOf(this.selectedToken)
                if (index < this.tokenOptions.length - 1) {
                    this.selectedToken = this.tokenOptions[index + 1]
                }
            } else if (event.key === "ArrowUp") {
                console.log("up")
                let index = this.tokenOptions.indexOf(this.selectedToken)
                if (index > 0) {
                    this.selectedToken = this.tokenOptions[index - 1]
                }
            } else if (event.key === "Enter") {
                this.makeGuess()
            } else {
                setTimeout(() => {
                    app.selectedToken = app.tokenOptions[0]
                    console.log(app.tokenOptions)
                    console.log(app.selectedToken)
                }, 100);
            }
        },
        guessClick: function(token) {
            this.selectedToken = token
            this.makeGuess();
        },
        makeGuess(skip=false) {
            let guess = this.selectedToken.replace("_", " ")
            this.guesses.push(guess)
            let token = this.unseen[0]

            if (guess == token) {  // Correct guess
                if (this.unseen.length <= 1) {  // Last token
                    this.win()
                }
                
                // Update stats
                this.guessHistory.push({
                    "index": this.index,
                    "guesses": this.guesses,
                    "token": token,
                    "skip": skip,
                    "id": this.passage_tokens[this.index].id
                })
                
                this.lastToken = token
                this.lastGPT2Guesses = this.passage_tokens[this.index].gpt2_guesses + 1

                if (skip) {
                    this.lastGuesses = "skipped"
                    this.passageGPT2SkipGuesses += this.lastGPT2Guesses
                    this.totalGPT2SkipGuesses += this.lastGPT2Guesses
                } else {
                    this.passageCorrect++
                    this.totalCorrect++
                    this.lastGuesses = this.guesses.length
                    this.passageGuesses += this.lastGuesses
                    this.totalGuesses += this.lastGuesses
                    this.passageGPT2Guesses += this.lastGPT2Guesses
                    this.totalGPT2Guesses += this.lastGPT2Guesses
                }
                

                // Reset
                let seen = this.seen
                let unseen = this.unseen
                let newSeen = seen + guess
                let newUnseen = unseen.slice(1, unseen.length)
                this.seen = newSeen
                this.unseen = newUnseen
                this.query = ""
                this.selectedToken = ""
                this.guesses = []
                this.index++
            
                
            } else {
                // Incorrect guess
            }
        },
        skipToken() {
            this.selectedToken = this.unseen[0]
            this.makeGuess(skip=true)
            this.passageSkips++
            this.totalSkips ++
        },
        win() {
            $('#winModal').modal("show")
            this.noPassages++
            this.saveGuesses();
        },
        newGame() {
            $('#winModal').modal("hide")
            this.getSentence()
            this.guesses = []
            this.query = ""
            this.selectedToken = ""
            this.passageGuesses = 0
            this.passageGPT2Guesses = 0
            this.passageCorrect = 0
            this.passageSkips = 0
            this.lastToken = ""
            this.lastGuesses = null
            this.lastGPT2Guesses = null

        },
        getSentence() {
            axios.post('/nwp/get_sentence/',
                {})
            .then(function (response) {
                console.log(response);
                app.passage = response.data.passage
                app.passage_tokens = response.data.tokens
                app.seen = app.passage_tokens[0].token
                app.unseen = app.passage_tokens.slice(1).map((token) => token.token)
                app.index = 1
            })
            .catch(function (error) {
                console.log(error);
            });

        },
        saveGuesses() {
            axios.post('/nwp/save_guesses/',
                {
                    "guesses": this.guessHistory,
                    "passage_id": this.passage.id,
                    "status": "complete"
                })
            .then(function (response) {
                console.log(response);
            })
            .catch(function (error) {
                console.log(error);
            });
        }
    }
  }).mount('#app')


// Initialize modal
$('#winModal').modal().modal('hide')
