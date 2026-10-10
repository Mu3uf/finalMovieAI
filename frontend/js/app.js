// ============================================================
// MOVIE AI - FRONTEND
// ============================================================


// ============================================================
// CONFIG
// ============================================================

const API_BASE_URL = "";

const TMDB_IMAGE_BASE_URL =
    "https://image.tmdb.org/t/p/w500";


// ============================================================
// AUTH STORAGE
// ============================================================

const ACCESS_TOKEN_KEY = "movieai_access_token";

const USER_KEY = "movieai_user";


// ============================================================
// DOM ELEMENTS
// ============================================================

const movieGrid =
    document.getElementById("movieGrid");

const moviesTitle =
    document.getElementById("moviesTitle");

const moviesDescription =
    document.getElementById("moviesDescription");

const moviesLabel =
    document.getElementById("moviesLabel");

const movieCount =
    document.getElementById("movieCount");

const chatMessages =
    document.getElementById("chatMessages");
const chatSection =
    document.querySelector(".chat-section");

const chatForm =
    document.getElementById("chatForm");

const chatInput =
    document.getElementById("chatInput");

const sendButton =
    document.getElementById("sendButton");

const likedButton =
    document.getElementById("likedButton");

const watchedButton =
    document.getElementById("watchedButton");

const loginButton =
    document.getElementById("loginButton");

const logoButton =
    document.getElementById("logoButton");


// ============================================================
// AUTH DOM
// ============================================================

const authModal =
    document.getElementById("authModal");

const closeAuthModal =
    document.getElementById("closeAuthModal");

const authForm =
    document.getElementById("authForm");

const authTitle =
    document.getElementById("authTitle");

const authDescription =
    document.getElementById("authDescription");

const authSubmit =
    document.getElementById("authSubmit");

const authSwitchText =
    document.getElementById("authSwitchText");

const authSwitchButton =
    document.getElementById("authSwitchButton");

const authEmail =
    document.getElementById("authEmail");

const authPassword =
    document.getElementById("authPassword");

const authError =
    document.getElementById("authError");


// ============================================================
// STATE
// ============================================================

let authMode = "login";

let currentUser = getStoredUser();

let currentMovies = [];


// ============================================================
// STORAGE HELPERS
// ============================================================

function getAccessToken() {

    return localStorage.getItem(
        ACCESS_TOKEN_KEY
    );

}


function getStoredUser() {

    try {

        const user =
            localStorage.getItem(
                USER_KEY
            );

        return user
            ? JSON.parse(user)
            : null;

    }

    catch (error) {

        console.error(
            "Failed to read stored user:",
            error
        );

        return null;

    }

}


function saveAuth(
    accessToken,
    user
) {

    localStorage.setItem(
        ACCESS_TOKEN_KEY,
        accessToken
    );

    localStorage.setItem(
        USER_KEY,
        JSON.stringify(user)
    );

    currentUser = user;

}


function clearAuth() {

    localStorage.removeItem(
        ACCESS_TOKEN_KEY
    );

    localStorage.removeItem(
        USER_KEY
    );

    currentUser = null;

}


// ============================================================
// AUTH HEADERS
// ============================================================

function getAuthHeaders() {

    const token =
        getAccessToken();

    if (!token) {

        return {};

    }

    return {

        Authorization:
            `Bearer ${token}`

    };

}


// ============================================================
// AUTH MODAL
// ============================================================

function openAuthModal(
    mode = "login"
) {

    authMode = mode;

    updateAuthModal();

    hideAuthError();

    authModal.classList.remove(
        "hidden"
    );

    setTimeout(
        () => authEmail.focus(),
        50
    );

}


function closeAuth() {

    authModal.classList.add(
        "hidden"
    );

    authForm.reset();

    hideAuthError();

}


function updateAuthModal() {

    if (authMode === "login") {

        authTitle.textContent =
            "Welcome back";

        authDescription.textContent =
            "Login to save your favorite movies.";

        authSubmit.textContent =
            "Login";

        authSwitchText.textContent =
            "Don't have an account?";

        authSwitchButton.textContent =
            "Sign up";

    }

    else {

        authTitle.textContent =
            "Create your account";

        authDescription.textContent =
            "Create an account to save movies you love.";

        authSubmit.textContent =
            "Create account";

        authSwitchText.textContent =
            "Already have an account?";

        authSwitchButton.textContent =
            "Login";

    }

}


function showAuthError(
    message
) {

    authError.textContent =
        message;

    authError.classList.remove(
        "hidden"
    );

}


function hideAuthError() {

    authError.textContent =
        "";

    authError.classList.add(
        "hidden"
    );

}


// ============================================================
// UPDATE LOGIN BUTTON
// ============================================================

function updateAuthUI() {

    if (currentUser) {

        loginButton.textContent =
            "Logout";

        loginButton.classList.add(
            "logged-in"
        );

    }

    else {

        loginButton.textContent =
            "Login";

        loginButton.classList.remove(
            "logged-in"
        );

    }

}


// ============================================================
// VERIFY CURRENT SESSION
// ============================================================

async function verifyCurrentUser() {

    const token =
        getAccessToken();

    if (!token) {

        updateAuthUI();

        return;

    }

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/auth/me`,
                {
                    headers:{
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {

            clearAuth();

            updateAuthUI();

            return;

        }

        const data =
            await response.json();

        if (
            data.success &&
            data.user
        ) {

            currentUser =
                data.user;

            localStorage.setItem(
                USER_KEY,
                JSON.stringify(
                    currentUser
                )
            );

        }

        updateAuthUI();

    }

    catch (error) {

        console.error(
            "Session verification error:",
            error
        );

        clearAuth();

        updateAuthUI();

    }

}


// ============================================================
// LOGIN
// ============================================================

async function login(
    email,
    password
) {

    const response = await fetch(
        `${API_BASE_URL}/api/auth/login`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "Login failed."
        );
    }

    if (!data.success || !data.access_token) {
        throw new Error(
            "Login failed."
        );
    }

    saveAuth(
        data.access_token,
        data.user
    );

    updateAuthUI();
}


// ============================================================
// SIGNUP
// ============================================================

async function signup(
    email,
    password
) {

    const response =
        await fetch(
            `${API_BASE_URL}/api/auth/signup`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    email,
                    password
                })
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Could not create account."
        );

    }

    return data;

}


// ============================================================
// AUTH FORM
// ============================================================

authForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        hideAuthError();

        const email =
            authEmail.value.trim();

        const password =
            authPassword.value;

        if (!email || !password) {

            showAuthError(
                "Please enter your email and password."
            );

            return;

        }

        authSubmit.disabled = true;

        try {

            if (authMode === "login") {

                await login(
                    email,
                    password
                );

                closeAuth();

                await refreshCurrentMovieActions();

            }

            else {

                const data =
                    await signup(
                        email,
                        password
                    );

                /*
                 * Supabase may require email
                 * confirmation depending on
                 * project settings.
                 */

                if (
                    data.user &&
                    data.access_token
                ) {

                    saveAuth(
                        data.access_token,
                        data.user
                    );

                    updateAuthUI();

                    closeAuth();

                    await refreshCurrentMovieActions();

                }

                else {

                    authMode = "login";

                    updateAuthModal();

                    showAuthError(
                        "Account created. Please check your email if confirmation is required, then login."
                    );

                }

            }

        }

        catch (error) {

            console.error(
                "Authentication error:",
                error
            );

            showAuthError(
                error.message ||
                "Authentication failed."
            );

        }

        finally {

            authSubmit.disabled =
                false;

        }

    }
);


// ============================================================
// AUTH SWITCH
// ============================================================

authSwitchButton.addEventListener(
    "click",
    () => {

        authMode =
            authMode === "login"
                ? "signup"
                : "login";

        updateAuthModal();

        hideAuthError();

        authPassword.value = "";

    }
);


// ============================================================
// CLOSE MODAL
// ============================================================

closeAuthModal.addEventListener(
    "click",
    closeAuth
);


authModal.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            authModal
        ) {

            closeAuth();

        }

    }
);


// ============================================================
// LOGIN / LOGOUT BUTTON
// ============================================================

loginButton.addEventListener(
    "click",
    async () => {

        if (currentUser) {

            const confirmed =
                confirm(
                    "Do you want to logout?"
                );

            if (!confirmed) {

                return;

            }

            clearAuth();

            updateAuthUI();

            /*
             * Reset current movie buttons
             * because user actions belong
             * to the logged-in user.
             */

            await refreshCurrentMovieActions();

            return;

        }

        openAuthModal(
            "login"
        );

    }
);


// ============================================================
// LOAD TRENDING MOVIES
// ============================================================

async function loadTrendingMovies() {

    setActiveNav(
        null
    );

    try {

        movieGrid.innerHTML = `
            <div class="empty-state">
                Loading trending movies...
            </div>
        `;

        const response =
            await fetch(
                `${API_BASE_URL}/api/movies/trending`
            );

        if (!response.ok) {

            throw new Error(
                "Failed to load trending movies."
            );

        }

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                data.message ||
                "Could not load trending movies."
            );

        }

        moviesLabel.textContent =
            "TMDB";

        moviesTitle.textContent =
            "Trending Movies";

        moviesDescription.textContent =
            "What's popular right now";

        movieCount.textContent =
            `${data.movies.length} movies`;

        renderMovies(
            data.movies
        );

    }

    catch (error) {

        console.error(
            "Trending error:",
            error
        );

        movieGrid.innerHTML = `
            <div class="empty-state">
                Unable to load trending movies.
            </div>
        `;

    }

}


// ============================================================
// RENDER MOVIES
// ============================================================

function renderMovies(
    movies
) {

    currentMovies =
        movies || [];

    movieGrid.innerHTML = "";

    if (
        !movies ||
        movies.length === 0
    ) {

        movieGrid.innerHTML = `
            <div class="empty-state">
                No movies found.
            </div>
        `;

        return;

    }


    movies.forEach(
        (movie, index) => {

            const card =
                createMovieCard(
                    movie,
                    index
                );

            movieGrid.appendChild(
                card
            );

        }
    );


    /*
     * After cards exist, retrieve
     * current user's Like/Watched
     * state.
     */

    refreshCurrentMovieActions();

}


// ============================================================
// CREATE MOVIE CARD
// ============================================================

function createMovieCard(
    movie,
    index = 0
) {

    const card =
        document.createElement(
            "article"
        );

    card.className =
        "movie-card";

    card.style.animationDelay =
        `${index * 0.06}s`;


    // --------------------------------------------------------
    // Movie information
    // --------------------------------------------------------

    const title =
        movie.title ||
        "Unknown title";

    const year =
        movie.release_year ||
        extractYear(
            movie.release_date
        );

    const rating =
        movie.rating !== null &&
        movie.rating !== undefined
            ? Number(
                movie.rating
            ).toFixed(1)
            : "N/A";

    const genres =
        Array.isArray(
            movie.genres
        )
            ? movie.genres.join(", ")
            : "Genre unavailable";


    // --------------------------------------------------------
    // Poster
    // --------------------------------------------------------

    let posterUrl = null;

    if (movie.poster_path) {

        if (
            movie.poster_path.startsWith(
                "http"
            )
        ) {

            posterUrl =
                movie.poster_path;

        }

        else {

            posterUrl =
                `${TMDB_IMAGE_BASE_URL}${movie.poster_path}`;

        }

    }


    // --------------------------------------------------------
    // Poster HTML
    // --------------------------------------------------------

    const posterHTML =
        posterUrl

            ? `
                <img
                    src="${escapeHTML(posterUrl)}"
                    alt="${escapeHTML(title)} poster"
                    loading="lazy"
                    onerror="this.style.display='none'"
                >
            `

            : `
                <div
                    style="
                        height:100%;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        color:#71717a;
                        font-size:12px;
                        text-align:center;
                        padding:20px;
                    "
                >
                    No poster available
                </div>
            `;


    // --------------------------------------------------------
    // Card HTML
    // --------------------------------------------------------

    card.innerHTML = `

        <div class="movie-poster">

            ${posterHTML}

            <div class="movie-rating">

                ⭐ ${rating}

            </div>

        </div>


        <div class="movie-info">


            <div class="movie-title">

                ${escapeHTML(title)}

            </div>


            <div class="movie-meta">

                <span>
                    ${year || "Year unknown"}
                </span>

                <span>•</span>

                <span>
                    ${escapeHTML(
                        movie.duration || ""
                    )}
                </span>

            </div>


            <div class="movie-genres">

                ${escapeHTML(genres)}

            </div>


            <div class="movie-actions">


                <button
                    class="movie-action like-button"
                    type="button"
                >
                    ♡ Like
                </button>


                <button
                    class="movie-action watched-button"
                    type="button"
                >
                    ◷ Watched
                </button>


            </div>


        </div>

    `;


    // --------------------------------------------------------
    // Like button
    // --------------------------------------------------------

    const likeButton =
        card.querySelector(
            ".like-button"
        );


    likeButton.addEventListener(
        "click",
        async () => {

            if (!currentUser) {

                openAuthModal(
                    "login"
                );

                return;

            }

            const currentlyLiked =
                likeButton.classList.contains(
                    "active"
                );

            await updateMovieAction(
                movie,
                {
                    liked:
                        !currentlyLiked
                },
                likeButton
            );

        }
    );


    // --------------------------------------------------------
    // Watched button
    // --------------------------------------------------------

    const watchedButton =
        card.querySelector(
            ".watched-button"
        );


    watchedButton.addEventListener(
        "click",
        async () => {

            if (!currentUser) {

                openAuthModal(
                    "login"
                );

                return;

            }

            const currentlyWatched =
                watchedButton.classList.contains(
                    "active"
                );

            await updateMovieAction(
                movie,
                {
                    watched:
                        !currentlyWatched
                },
                watchedButton
            );

        }
    );


    return card;

}


// ============================================================
// UPDATE MOVIE ACTION
// ============================================================

async function updateMovieAction(
    movie,
    action,
    button
) {

    if (!movie.imdb_id) {

        alert(
            "This movie cannot be saved because it has no IMDb ID."
        );

        return;

    }


    button.classList.add(
        "loading-action"
    );


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/movies/action`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        ...getAuthHeaders()
                    },

                    body: JSON.stringify({

                        imdb_id:
                            movie.imdb_id,

                        ...action

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (
                response.status === 401
            ) {

                clearAuth();

                updateAuthUI();

                openAuthModal(
                    "login"
                );

                throw new Error(
                    "Please login again."
                );

            }


            throw new Error(
                data.detail ||
                "Could not save movie action."
            );

        }


        if (!data.success) {

            throw new Error(
                data.message ||
                "Could not save movie action."
            );

        }


        /*
         * Refresh all buttons on the
         * current cards.
         */

        await refreshCurrentMovieActions();

    }

    catch (error) {

        console.error(
            "Movie action error:",
            error
        );

        alert(
            error.message ||
            "Could not save movie action."
        );

    }

    finally {

        button.classList.remove(
            "loading-action"
        );

    }

}


// ============================================================
// REFRESH CURRENT MOVIE ACTIONS
// ============================================================

async function refreshCurrentMovieActions() {

    if (!currentUser) {

        resetMovieActionButtons();

        return;

    }


    if (
        !currentMovies ||
        currentMovies.length === 0
    ) {

        return;

    }


    try {

        const [
            likedResponse,
            watchedResponse
        ] = await Promise.all([

            fetch(
                `${API_BASE_URL}/api/movies/liked`,
                {
                    headers:
                        getAuthHeaders()
                }
            ),

            fetch(
                `${API_BASE_URL}/api/movies/watched`,
                {
                    headers:
                        getAuthHeaders()
                }
            )

        ]);


        if (
            likedResponse.status === 401 ||
            watchedResponse.status === 401
        ) {

            clearAuth();

            updateAuthUI();

            resetMovieActionButtons();

            return;

        }


        if (
            !likedResponse.ok ||
            !watchedResponse.ok
        ) {

            return;

        }


        const likedData =
            await likedResponse.json();

        const watchedData =
            await watchedResponse.json();


        const likedIds =
            new Set(
                (likedData.movies || [])
                    .map(
                        movie =>
                            movie.imdb_id
                    )
            );


        const watchedIds =
            new Set(
                (watchedData.movies || [])
                    .map(
                        movie =>
                            movie.imdb_id
                    )
            );


        const cards =
            movieGrid.querySelectorAll(
                ".movie-card"
            );


        cards.forEach(
            (card, index) => {

                const movie =
                    currentMovies[index];

                if (!movie) {

                    return;

                }


                const likeButton =
                    card.querySelector(
                        ".like-button"
                    );


                const watchedButton =
                    card.querySelector(
                        ".watched-button"
                    );


                const isLiked =
                    likedIds.has(
                        movie.imdb_id
                    );


                const isWatched =
                    watchedIds.has(
                        movie.imdb_id
                    );


                setLikeButtonState(
                    likeButton,
                    isLiked
                );


                setWatchedButtonState(
                    watchedButton,
                    isWatched
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Failed to refresh movie actions:",
            error
        );

    }

}


// ============================================================
// RESET ACTION BUTTONS
// ============================================================

function resetMovieActionButtons() {

    const cards =
        movieGrid.querySelectorAll(
            ".movie-card"
        );


    cards.forEach(
        card => {

            const likeButton =
                card.querySelector(
                    ".like-button"
                );

            const watchedButton =
                card.querySelector(
                    ".watched-button"
                );


            setLikeButtonState(
                likeButton,
                false
            );


            setWatchedButtonState(
                watchedButton,
                false
            );

        }
    );

}


// ============================================================
// LIKE BUTTON STATE
// ============================================================

function setLikeButtonState(
    button,
    active
) {

    if (!button) {

        return;

    }


    if (active) {

        button.classList.add(
            "active"
        );

        button.textContent =
            "♥ Liked";

    }

    else {

        button.classList.remove(
            "active"
        );

        button.textContent =
            "♡ Like";

    }

}


// ============================================================
// WATCHED BUTTON STATE
// ============================================================

function setWatchedButtonState(
    button,
    active
) {

    if (!button) {

        return;

    }


    if (active) {

        button.classList.add(
            "active"
        );

        button.textContent =
            "✓ Watched";

    }

    else {

        button.classList.remove(
            "active"
        );

        button.textContent =
            "◷ Watched";

    }

}


// ============================================================
// LOAD LIKED MOVIES
// ============================================================

async function loadLikedMovies() {

    if (!currentUser) {

        openAuthModal(
            "login"
        );

        return;

    }


    try {

        showMoviesLoading(
            "Loading your liked movies..."
        );


        const response =
            await fetch(
                `${API_BASE_URL}/api/movies/liked`,
                {
                    headers:
                        getAuthHeaders()
                }
            );


        const data =
            await response.json();


        if (
            response.status === 401
        ) {

            clearAuth();

            updateAuthUI();

            openAuthModal(
                "login"
            );

            return;

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load liked movies."
            );

        }


        moviesLabel.textContent =
            "YOUR COLLECTION";

        moviesTitle.textContent =
            "Liked Movies";

        moviesDescription.textContent =
            "Movies you've saved as favorites";

        movieCount.textContent =
            `${(data.movies || []).length} movies`;


        setActiveNav(
            "liked"
        );


        renderMovies(
            data.movies || []
        );

    }

    catch (error) {

        console.error(
            "Liked movies error:",
            error
        );

        movieGrid.innerHTML = `
            <div class="empty-state">
                Unable to load liked movies.
            </div>
        `;

    }

}


// ============================================================
// LOAD WATCHED MOVIES
// ============================================================

async function loadWatchedMovies() {

    if (!currentUser) {

        openAuthModal(
            "login"
        );

        return;

    }


    try {

        showMoviesLoading(
            "Loading your watched movies..."
        );


        const response =
            await fetch(
                `${API_BASE_URL}/api/movies/watched`,
                {
                    headers:
                        getAuthHeaders()
                }
            );


        const data =
            await response.json();


        if (
            response.status === 401
        ) {

            clearAuth();

            updateAuthUI();

            openAuthModal(
                "login"
            );

            return;

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load watched movies."
            );

        }


        moviesLabel.textContent =
            "YOUR COLLECTION";

        moviesTitle.textContent =
            "Watched Movies";

        moviesDescription.textContent =
            "Movies you've already watched";

        movieCount.textContent =
            `${(data.movies || []).length} movies`;


        setActiveNav(
            "watched"
        );


        renderMovies(
            data.movies || []
        );

    }

    catch (error) {

        console.error(
            "Watched movies error:",
            error
        );

        movieGrid.innerHTML = `
            <div class="empty-state">
                Unable to load watched movies.
            </div>
        `;

    }

}


// ============================================================
// SHOW MOVIES LOADING
// ============================================================

function showMoviesLoading(
    message
) {

    movieGrid.innerHTML = `
        <div class="empty-state">
            ${escapeHTML(message)}
        </div>
    `;

}


// ============================================================
// NAV ACTIVE STATE
// ============================================================

function setActiveNav(
    active
) {

    likedButton.classList.toggle(
        "active",
        active === "liked"
    );

    watchedButton.classList.toggle(
        "active",
        active === "watched"
    );

}


// ============================================================
// LOGO = TRENDING
// ============================================================

logoButton.addEventListener(
    "click",
    () => {

        loadTrendingMovies();

    }
);


// ============================================================
// LIKED NAVIGATION
// ============================================================

likedButton.addEventListener(
    "click",
    () => {

        loadLikedMovies();

    }
);


// ============================================================
// WATCHED NAVIGATION
// ============================================================

watchedButton.addEventListener(
    "click",
    () => {

        loadWatchedMovies();

    }
);


// ============================================================
// SEND CHAT MESSAGE
// ============================================================

async function sendChatMessage(
    message
) {

    if (!message.trim()) {
        return;
    }

    if (sendButton.disabled) {
        return;
    }

    addUserMessage(message);

    chatInput.value = "";

    setChatLoading(true);

    try {

        const accessToken = getAccessToken();

        if (!accessToken) {
            openAuthModal("login");

            throw new Error(
                "Please log in to send a message."
            );
        }

        const response = await fetch(
            `${API_BASE_URL}/api/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${accessToken}`
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Chat request failed."
            );
        }

        addAssistantMessage(
            data.message ||
            "I couldn't generate a response."
        );

        if (
            data.movies &&
            data.movies.length > 0
        ) {

            moviesLabel.textContent =
                "AI RECOMMENDATIONS";

            moviesTitle.textContent =
                "Recommended Movies";

            moviesDescription.textContent =
                "Selected by your AI movie assistant";

            movieCount.textContent =
                `${data.movies.length} movies`;

            setActiveNav(null);

            renderMovies(data.movies);
        }

    } catch (error) {

        console.error(
            "Chat error:",
            error
        );

        addAssistantMessage(
            "Sorry, something went wrong while processing your request."
        );

    } finally {

        setChatLoading(false);

        chatInput.focus();
    }
}


// ============================================================
// CHAT FORM
// ============================================================

chatForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const message =
            chatInput.value.trim();


        if (!message) {

            return;

        }


        await sendChatMessage(
            message
        );

    }
);


// ============================================================
// USER MESSAGE
// ============================================================

function addUserMessage(
    message
) {

    const messageElement =
        document.createElement(
            "div"
        );


    messageElement.className =
        "message user-message";


    messageElement.innerHTML = `

        <div class="message-content">

            ${escapeHTML(message)}

        </div>

    `;


    chatMessages.appendChild(
        messageElement
    );


    scrollChatToBottom();

}


// ============================================================
// ASSISTANT MESSAGE
// ============================================================

function addAssistantMessage(
    message
) {

    const messageElement =
        document.createElement(
            "div"
        );


    messageElement.className =
        "message assistant-message";


    messageElement.innerHTML = `

        <div class="message-avatar">
            AI
        </div>


        <div class="message-content">

            ${formatMessage(message)}

        </div>

    `;


    chatMessages.appendChild(
        messageElement
    );


    scrollChatToBottom();

}


// ============================================================
// LOADING
// ============================================================

function setChatLoading(
    loading
) {

    sendButton.disabled =
        loading;

    chatInput.disabled =
        loading;
    if (chatSection) {
    chatSection.classList.toggle(
        "is-loading",
        loading
    );
    
   }

    const existingLoader =
        document.getElementById(
            "chatLoading"
        );


    if (loading) {

        if (existingLoader) {

            return;

        }


        const loader =
            document.createElement(
                "div"
            );


        loader.id =
            "chatLoading";


        loader.className =
            "message assistant-message";


        loader.innerHTML = `

            <div class="message-avatar">
                AI
            </div>


            <div class="message-content">

                <div class="loading">

                    <span></span>

                    <span></span>

                    <span></span>

                </div>

            </div>

        `;


        chatMessages.appendChild(
            loader
        );


        scrollChatToBottom();

    }

    else {

        if (existingLoader) {

            existingLoader.remove();

        }

    }

}


// ============================================================
// SUGGESTION BUTTONS
// ============================================================

document
    .querySelectorAll(
        ".suggestion-button"
    )
    .forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const text =
                        button.textContent.trim();

                    chatInput.value =
                        text;

                    chatInput.focus();

                }
            );

        }
    );


// ============================================================
// SCROLL CHAT
// ============================================================

function scrollChatToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


// ============================================================
// FORMAT MESSAGE
// ============================================================

function formatMessage(
    message
) {

    if (!message) {

        return "";

    }


    let text =
        escapeHTML(
            String(message)
        );


    text =
        text.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    text =
        text.replace(
            /\n/g,
            "<br>"
        );


    return text;

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// ============================================================
// EXTRACT YEAR
// ============================================================

function extractYear(
    releaseDate
) {

    if (!releaseDate) {

        return null;

    }


    const match =
        String(
            releaseDate
        ).match(
            /^\d{4}/
        );


    return match
        ? match[0]
        : null;

}


// ============================================================
// INITIALIZE
// ============================================================

async function initialize() {

    updateAuthUI();

    await verifyCurrentUser();

    await loadTrendingMovies();

    chatInput.focus();

}



initialize();

const discoverButton =
    document.getElementById("discoverButton");

if (discoverButton) {
    discoverButton.addEventListener(
        "click",
        () => {
            loadTrendingMovies();
        }
    );
}