from app.server.interview.sessions.session_initializer import SessionInitializer


def main() -> None:
    initializer = SessionInitializer()
    result = initializer.initialize("zzhang32@usc.edu")

    print("Candidate Loaded:")
    print(result.candidate)
    print()

    print("Resume Loaded:")
    print(result.resume)
    print()

    print("Session Created:")
    print(result.session)
    print()

    print("Profile Initialized:")
    print(result.profile)
    print()

    print("Experience Evidence Initialized:")
    print(result.evidence)
    print()

    print("Ready for intro phase.")


if __name__ == "__main__":
    main()