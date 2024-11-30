import asyncio
import lsr
import lsr_cars


def main():
    asyncio.run(lsr.main())
    asyncio.run(lsr_cars.main())


if __name__ == '__main__':
    main()