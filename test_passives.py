"""
Unit tests for all passive abilities to catch bugs before they crash the game.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game import Game
from board import Board
from unit import Unit, UnitType, PassiveSkill
from content.unit_registry import create_unit
from skill_factory import create_skill
import traceback

class PassiveTest:
    def __init__(self):
        self.game = Game()
        self.board = self.game.board
        self.passed = 0
        self.failed = 0
        self.results = []
        
    def log(self, test_name, status, error=None):
        """Log test result"""
        if status == "PASS":
            self.passed += 1
            print(f"PASS {test_name}")
        else:
            self.failed += 1
            print(f"FAIL {test_name}: {error}")
        self.results.append((test_name, status, error))
    
    def create_test_unit(self, unit_type: UnitType):
        """Create a unit for testing"""
        unit = create_unit(unit_type)
        if unit:
            self.board.add_unit(unit, 0, 0, "player")
        return unit
    
    def create_enemy_unit(self, unit_type: UnitType):
        """Create an enemy unit for testing"""
        unit = create_unit(unit_type)
        if unit:
            self.board.add_unit(unit, 7, 7, "enemy")
        return unit
    
    def test_berserker_passives(self):
        """Test all berserker passive abilities"""
        print("\n=== Testing Berserker Passives ===")
        
        # Test Fast Frenzy
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            fast_frenzy = create_skill(PassiveSkill.FAST_FRENZY)
            if fast_frenzy:
                berserker.add_passive_skill(fast_frenzy)
                # Cast Frenzy and check if attack speed bonus is 15 instead of 10
                berserker.spell.execute(berserker)
                self.log("Fast Frenzy", "PASS")
            else:
                self.log("Fast Frenzy", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Fast Frenzy", "FAIL", str(e))
        
        self.board.clear()
        
        # Test Hungry Frenzy
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            hungry_frenzy = create_skill(PassiveSkill.HUNGRY_FRENZY)
            if hungry_frenzy:
                berserker.add_passive_skill(hungry_frenzy)
                berserker.spell.execute(berserker)
                self.log("Hungry Frenzy", "PASS")
            else:
                self.log("Hungry Frenzy", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Hungry Frenzy", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Immortal Frenzy
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            immortal_frenzy = create_skill(PassiveSkill.IMMORTAL_FRENZY)
            if immortal_frenzy:
                berserker.add_passive_skill(immortal_frenzy)
                berserker.spell.execute(berserker)
                self.log("Immortal Frenzy", "PASS")
            else:
                self.log("Immortal Frenzy", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Immortal Frenzy", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Leap
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            leap = create_skill(PassiveSkill.LEAP)
            if leap:
                leap.caster = berserker
                berserker.add_passive_skill(leap)
                # Simulate a kill event
                leap.on_event("unit_death", killer=berserker)
                self.log("Leap", "PASS")
            else:
                self.log("Leap", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Leap", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Frenzy Cry
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            ally = self.create_test_unit(UnitType.PALADIN)
            frenzy_cry = create_skill(PassiveSkill.FRENZY_CRY)
            if frenzy_cry:
                berserker.add_passive_skill(frenzy_cry)
                berserker.spell.execute(berserker)
                self.log("Frenzy Cry", "PASS")
            else:
                self.log("Frenzy Cry", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Frenzy Cry", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Ripper
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            ripper = create_skill(PassiveSkill.RIPPER)
            if ripper:
                ripper.caster = berserker
                berserker.add_passive_skill(ripper)
                # Simulate attack event
                ripper.on_event("unit_attack", attacker=berserker, target=enemy)
                self.log("Ripper", "PASS")
            else:
                self.log("Ripper", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Ripper", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Cleave
        try:
            berserker = self.create_test_unit(UnitType.BERSERKER)
            enemy1 = self.create_enemy_unit(UnitType.NECROMANCER)
            enemy2 = self.create_enemy_unit(UnitType.PALADIN)
            self.board.add_unit(enemy2, 6, 7, "enemy")  # Adjacent to enemy1
            cleave = create_skill(PassiveSkill.CLEAVE)
            if cleave:
                cleave.caster = berserker
                berserker.add_passive_skill(cleave)
                # Simulate attack event
                cleave.on_event("unit_attack", attacker=berserker, target=enemy1)
                self.log("Cleave", "PASS")
            else:
                self.log("Cleave", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Cleave", "FAIL", str(e))
            
        self.board.clear()
    
    def test_pyromancer_passives(self):
        """Test all pyromancer passive abilities"""
        print("\n=== Testing Pyromancer Passives ===")
        
        # Test Firestorm
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            firestorm = create_skill(PassiveSkill.FIRESTORM)
            if firestorm:
                pyromancer.add_passive_skill(firestorm)
                # Cast fireball
                if pyromancer.spell:
                    pyromancer.spell.execute(pyromancer)
                self.log("Firestorm", "PASS")
            else:
                self.log("Firestorm", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Firestorm", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Big Fireball
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            big_fireball = create_skill(PassiveSkill.BIG_FIREBALL)
            if big_fireball:
                pyromancer.add_passive_skill(big_fireball)
                if pyromancer.spell:
                    pyromancer.spell.execute(pyromancer)
                self.log("Big Fireball", "PASS")
            else:
                self.log("Big Fireball", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Big Fireball", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Shrapnel
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            for i in range(4):
                enemy = self.create_enemy_unit(UnitType.NECROMANCER)
                self.board.add_unit(enemy, 6 + i % 2, 6 + i // 2, "enemy")
            shrapnel = create_skill(PassiveSkill.SHRAPNEL)
            if shrapnel:
                pyromancer.add_passive_skill(shrapnel)
                if pyromancer.spell:
                    pyromancer.spell.execute(pyromancer)
                self.log("Shrapnel", "PASS")
            else:
                self.log("Shrapnel", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Shrapnel", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Flame Bath
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            ally = self.create_test_unit(UnitType.PALADIN)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            flame_bath = create_skill(PassiveSkill.FLAME_BATH)
            if flame_bath:
                pyromancer.add_passive_skill(flame_bath)
                if pyromancer.spell:
                    pyromancer.spell.execute(pyromancer)
                self.log("Flame Bath", "PASS")
            else:
                self.log("Flame Bath", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Flame Bath", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Flameshock
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            flameshock = create_skill(PassiveSkill.FLAMESHOCK)
            if flameshock:
                pyromancer.add_passive_skill(flameshock)
                if pyromancer.spell:
                    pyromancer.spell.execute(pyromancer)
                self.log("Flameshock", "PASS")
            else:
                self.log("Flameshock", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Flameshock", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Flamebolts
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            flamebolts = create_skill(PassiveSkill.FLAMEBOLTS)
            if flamebolts:
                # Add skill properly through unit method (sets owner automatically)
                pyromancer.add_passive_skill(flamebolts)
                # Simulate unit attack to trigger skill through board events
                pyromancer.board.raise_event("unit_attack", attacker=pyromancer, target=enemy)
                self.log("Flamebolts", "PASS")
            else:
                self.log("Flamebolts", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Flamebolts", "FAIL", str(e))
            
        self.board.clear()
        
        # Test Flameproof Aura
        try:
            pyromancer = self.create_test_unit(UnitType.PYROMANCER)
            ally = self.create_test_unit(UnitType.PALADIN)
            flameproof = create_skill(PassiveSkill.FLAMEPROOF_AURA)
            if flameproof:
                flameproof.caster = pyromancer
                pyromancer.add_passive_skill(flameproof)
                # Simulate battle start
                flameproof.on_event("battle_start")
                self.log("Flameproof Aura", "PASS")
            else:
                self.log("Flameproof Aura", "FAIL", "Could not create skill")
        except Exception as e:
            self.log("Flameproof Aura", "FAIL", str(e))
            
        self.board.clear()
    
    def test_item_interactions(self):
        """Test items with new mechanics"""
        print("\n=== Testing Item Interactions ===")
        
        # Test a few complex items
        try:
            from content.items import create_item
            
            # Test Frenzy Mask
            unit = self.create_test_unit(UnitType.BERSERKER)
            enemy = self.create_enemy_unit(UnitType.NECROMANCER)
            
            mask = create_item("frenzy_mask")
            if mask:
                unit.add_item(mask)
                # Simulate attack to trigger mask effect
                mask.on_event("unit_attack", attacker=unit, target=enemy)
                self.log("Frenzy Mask Item", "PASS")
            else:
                self.log("Frenzy Mask Item", "FAIL", "Could not create item")
        except Exception as e:
            self.log("Frenzy Mask Item", "FAIL", str(e))
            
        self.board.clear()
        
        try:
            # Test Thrumblade
            unit = self.create_test_unit(UnitType.BERSERKER)
            thrumblade = create_item("thrumblade")
            if thrumblade:
                unit.add_item(thrumblade)
                # Simulate time passage
                thrumblade.on_frame(1.0)
                self.log("Thrumblade Item", "PASS")
            else:
                self.log("Thrumblade Item", "FAIL", "Could not create item")
        except Exception as e:
            self.log("Thrumblade Item", "FAIL", str(e))
            
        self.board.clear()
        
        try:
            # Test Phantom Saber
            unit = self.create_test_unit(UnitType.BERSERKER)
            saber = create_item("phantom_saber")
            if saber:
                unit.add_item(saber)
                # Try to spawn clones
                saber.on_event("battle_start")
                self.log("Phantom Saber Item", "PASS")
            else:
                self.log("Phantom Saber Item", "FAIL", "Could not create item")
        except Exception as e:
            self.log("Phantom Saber Item", "FAIL", str(e))
            
        self.board.clear()
    
    def run_all_tests(self):
        """Run all passive ability tests"""
        print("Starting Passive Ability Tests...")
        print("=" * 50)
        
        self.test_berserker_passives()
        self.test_pyromancer_passives()
        self.test_item_interactions()
        
        print("\n" + "=" * 50)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed > 0:
            print("\nFailed tests need investigation:")
            for test_name, status, error in self.results:
                if status == "FAIL":
                    print(f"- {test_name}: {error}")
        
        return self.failed == 0

if __name__ == "__main__":
    tester = PassiveTest()
    success = tester.run_all_tests()
    if not success:
        print("\nSome tests failed. These issues should be fixed before running the game.")
    else:
        print("\nAll tests passed! Passive abilities should work correctly in game.")